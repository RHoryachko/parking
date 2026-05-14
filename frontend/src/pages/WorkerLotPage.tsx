import { useCallback, useEffect, useMemo, useState } from "react";
import {
  barrierAction,
  getWorkerParkingDetail,
  getWorkerSpotBoard,
  listWorkerParkings,
  registerEntry,
  registerExit,
  registerExitByPlate,
  searchVehiclesByPlate,
  workerCreateBooking,
  workerPayBooking,
} from "../api/worker";
import type {
  BookingWithPayments,
  Parking,
  ParkingDetail,
  Vehicle,
  WorkerSpotBoardItem,
} from "../types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Input } from "../components/Input";
import { Modal } from "../components/Modal";

function toLocalDatetimeValue(d: Date) {
  const p = (n: number) => n.toString().padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function defaultDatetimeRange() {
  const start = new Date();
  start.setSeconds(0, 0);
  start.setMinutes(0);
  start.setHours(start.getHours() + 1);
  const end = new Date(start);
  end.setHours(end.getHours() + 2);
  return { start: toLocalDatetimeValue(start), end: toLocalDatetimeValue(end) };
}

function spotTone(status: string) {
  if (status === "free") return "border-emerald-200 bg-emerald-50/80 text-emerald-950";
  if (status === "reserved") return "border-amber-200 bg-amber-50/80 text-amber-950";
  if (status === "occupied") return "border-rose-200 bg-rose-50/80 text-rose-950";
  return "border-zinc-200 bg-zinc-100 text-zinc-700";
}

function normalizePlateLocal(raw: string) {
  return raw.replace(/[\s-]/g, "").toUpperCase();
}

export function WorkerLotPage() {
  const [parkings, setParkings] = useState<Parking[]>([]);
  const [parkingId, setParkingId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ParkingDetail | null>(null);
  const [board, setBoard] = useState<WorkerSpotBoardItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [modalRow, setModalRow] = useState<WorkerSpotBoardItem | null>(null);

  const [plateQuery, setPlateQuery] = useState("");
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [bookingSpotId, setBookingSpotId] = useState<number | "">("");
  const [bookingTariffId, setBookingTariffId] = useState<number | "">("");
  const range = useMemo(() => defaultDatetimeRange(), []);
  const [plannedStart, setPlannedStart] = useState(range.start);
  const [plannedEnd, setPlannedEnd] = useState(range.end);
  const [bookingMsg, setBookingMsg] = useState<string | null>(null);
  const [plateSearchMsg, setPlateSearchMsg] = useState<string | null>(null);
  const [lastCreated, setLastCreated] = useState<BookingWithPayments | null>(null);

  const [exitPlateQuery, setExitPlateQuery] = useState("");
  const [exitPlateMsg, setExitPlateMsg] = useState<string | null>(null);

  const reloadBoard = useCallback(async () => {
    if (!parkingId) return;
    setLoadError(null);
    try {
      const [d, b] = await Promise.all([getWorkerParkingDetail(parkingId), getWorkerSpotBoard(parkingId)]);
      setDetail(d);
      setBoard(b);
    } catch {
      setLoadError("Не вдалося завантажити дані майданчика.");
      setDetail(null);
      setBoard([]);
    }
  }, [parkingId]);

  useEffect(() => {
    listWorkerParkings()
      .then((list) => {
        setParkings(list);
        if (list.length === 1) setParkingId(list[0].id);
      })
      .catch(() => setParkings([]));
  }, []);

  useEffect(() => {
    if (parkingId) void reloadBoard();
  }, [parkingId, reloadBoard]);

  useEffect(() => {
    if (detail?.tariffs?.length && bookingTariffId === "") {
      setBookingTariffId(detail.tariffs[0].id);
    }
  }, [detail, bookingTariffId]);

  const overstayRows = board.filter((r) => (r.overstay_minutes ?? 0) > 0);

  function onPlateInputChange(value: string) {
    setPlateQuery(value);
    if (selectedVehicle && normalizePlateLocal(value) !== normalizePlateLocal(selectedVehicle.plate_number)) {
      setSelectedVehicle(null);
    }
  }

  async function onBarrier(action: "open" | "close") {
    if (!parkingId) {
      window.alert("Оберіть паркінг.");
      return;
    }
    setBusy(true);
    try {
      await barrierAction({ parking_id: parkingId, action });
      window.alert(action === "open" ? "Шлагбаум відкрито." : "Шлагбаум закрито.");
    } catch {
      window.alert("Не вдалося відправити команду на шлагбаум.");
    } finally {
      setBusy(false);
    }
  }

  async function searchPlate() {
    setPlateSearchMsg(null);
    setBookingMsg(null);
    const q = plateQuery.trim();
    if (!q) {
      setVehicles([]);
      setPlateSearchMsg("Введіть номерний знак.");
      return;
    }
    setBusy(true);
    try {
      const rows = await searchVehiclesByPlate(q);
      setVehicles(rows);
      if (rows.length === 1) setSelectedVehicle(rows[0]);
      if (rows.length === 0) {
        setPlateSearchMsg("Нічого не знайдено. Перевірте номер.");
      } else {
        setPlateSearchMsg(`Знайдено: ${rows.length}. Оберіть авто нижче.`);
      }
    } catch {
      setVehicles([]);
      setPlateSearchMsg("Пошук за номером не вдався.");
    } finally {
      setBusy(false);
    }
  }

  async function submitBooking() {
    setBookingMsg(null);
    if (!parkingId || bookingSpotId === "" || bookingTariffId === "") {
      setBookingMsg("Оберіть паркінг, вільне місце та тариф.");
      return;
    }
    const plateNorm = normalizePlateLocal(plateQuery);
    if (!plateNorm) {
      setBookingMsg("Вкажіть номерний знак авто в блоці реєстрації бронювання.");
      return;
    }

    let vehicle = selectedVehicle;
    if (!vehicle || normalizePlateLocal(vehicle.plate_number) !== plateNorm) {
      setBusy(true);
      try {
        const rows = await searchVehiclesByPlate(plateQuery.trim());
        setVehicles(rows);
        if (rows.length === 0) {
          setSelectedVehicle(null);
          setBookingMsg("Авто з таким номером не знайдено. Перевірте номер.");
          return;
        }
        if (rows.length > 1) {
          setSelectedVehicle(null);
          setPlateSearchMsg(`За номером знайдено ${rows.length} записів — оберіть потрібне авто у блоці «Пошук авто за номером».`);
          setBookingMsg("Кілька авто з цим номером. Оберіть запис у блоці пошуку вище.");
          return;
        }
        vehicle = rows[0];
        setSelectedVehicle(vehicle);
      } catch {
        setBookingMsg("Не вдалося перевірити номер авто. Спробуйте ще раз.");
        return;
      } finally {
        setBusy(false);
      }
    }

    const start = new Date(plannedStart);
    const end = new Date(plannedEnd);
    if (!(end > start)) {
      setBookingMsg("Кінець має бути пізніше за початок.");
      return;
    }
    if (!vehicle) {
      setBookingMsg("Не вдалося визначити авто за номером.");
      return;
    }
    setBusy(true);
    try {
      const created = await workerCreateBooking({
        user_id: selectedVehicle.user_id,
        vehicle_id: selectedVehicle.id,
        parking_id: parkingId,
        spot_id: Number(bookingSpotId),
        tariff_id: Number(bookingTariffId),
        planned_start_time: start.toISOString(),
        planned_end_time: end.toISOString(),
      });
      setLastCreated(created);
      setBookingMsg(`Бронювання #${created.id} створено (статус: ${created.status}).`);
      await reloadBoard();
    } catch {
      setBookingMsg("Не вдалося створити бронювання (місце зайняте або конфлікт часу).");
    } finally {
      setBusy(false);
    }
  }

  async function payLastOr(bookingId: number) {
    setBusy(true);
    try {
      await workerPayBooking(bookingId);
      window.alert("Статус бронювання змінено на «оплачено».");
      setLastCreated(null);
      await reloadBoard();
      setModalRow(null);
    } catch {
      window.alert("Оплату не застосовано (перевірте статус бронювання).");
    } finally {
      setBusy(false);
    }
  }

  async function entryFromModal(row: WorkerSpotBoardItem) {
    if (!parkingId || !row.vehicle) return;
    setBusy(true);
    try {
      await registerEntry({ parking_id: parkingId, plate_number: row.vehicle.plate_number });
      window.alert("В’їзд зареєстровано, сесію відкрито.");
      await reloadBoard();
      setModalRow(null);
    } catch {
      window.alert("Не вдалося зареєструвати в’їзд (перевірте оплату та вікно бронювання).");
    } finally {
      setBusy(false);
    }
  }

  async function exitFromModal(sessionId: number) {
    setBusy(true);
    try {
      await registerExit({ session_id: sessionId });
      window.alert("Сесію парковки завершено.");
      await reloadBoard();
      setModalRow(null);
    } catch {
      window.alert("Не вдалося завершити сесію.");
    } finally {
      setBusy(false);
    }
  }

  async function submitExitByPlate() {
    setExitPlateMsg(null);
    if (!parkingId) {
      setExitPlateMsg("Оберіть паркінг.");
      return;
    }
    const plate = exitPlateQuery.trim();
    if (!plate) {
      setExitPlateMsg("Введіть номерний знак.");
      return;
    }
    setBusy(true);
    try {
      const s = await registerExitByPlate({ parking_id: parkingId, plate_number: plate });
      const price = s.total_price != null ? `${s.total_price} UAH` : "—";
      window.alert(`Виїзд зареєстровано. Сесія #${s.id}, сума: ${price}.`);
      setExitPlateQuery("");
      await reloadBoard();
    } catch {
      setExitPlateMsg("Немає активної сесії з цим номером на цьому майданчику (або помилка сервера).");
    } finally {
      setBusy(false);
    }
  }

  const freeSpots = board.filter((r) => r.spot.status === "free");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold tracking-tight text-zinc-900">Робочий майданчик</div>
          <div className="mt-1 text-sm text-zinc-600">
            Місця, шлагбаум, в’їзд/виїзд за номером, бронювання та оплата в одному вікні.
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" disabled={busy || !parkingId} onClick={() => void reloadBoard()}>
            Оновити сітку
          </Button>
        </div>
      </div>

      <Card>
        <div className="text-sm font-semibold text-zinc-900">Паркінг</div>
        {parkings.length === 0 ? (
          <div className="mt-2 text-sm text-zinc-600">Немає призначених паркінгів. Зверніться до адміністратора.</div>
        ) : (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <label className="text-sm text-zinc-600">
              Оберіть майданчик
              <select
                className="ml-2 rounded-xl border border-black/10 bg-white px-3 py-2 text-sm font-medium text-zinc-900"
                value={parkingId ?? ""}
                onChange={(e) => setParkingId(Number(e.target.value) || null)}
              >
                <option value="">—</option>
                {parkings.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.city})
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
      </Card>

      {parkingId ? (
        <>
          <Card>
            <div className="text-sm font-semibold text-zinc-900">Шлагбаум</div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button type="button" disabled={busy} onClick={() => void onBarrier("open")}>
                Відкрити шлагбаум
              </Button>
              <Button type="button" variant="secondary" disabled={busy} onClick={() => void onBarrier("close")}>
                Закрити шлагбаум
              </Button>
            </div>
            <p className="mt-2 text-xs text-zinc-500">Після успішної команди з’явиться системне повідомлення.</p>
          </Card>

          <Card>
            <div className="text-sm font-semibold text-zinc-900">Реєстрація виїзду</div>
            <p className="mt-1 text-xs text-zinc-500">
              Держномер авто, що виїжджає з цього майданчика. Час виїзду та сума зараховуються автоматично. Можна також
              натиснути місце на сітці й обрати «Завершити сесію (виїзд)».
            </p>
            <div className="mt-4 flex max-w-xl flex-wrap gap-2">
              <Input
                className="min-w-[200px] flex-1 font-mono"
                value={exitPlateQuery}
                onChange={(e) => setExitPlateQuery(e.target.value)}
                placeholder="AA1234BC"
                autoComplete="off"
              />
              <Button type="button" variant="secondary" disabled={busy || !parkingId} onClick={() => void submitExitByPlate()}>
                Зареєструвати виїзд
              </Button>
            </div>
            {exitPlateMsg ? <div className="mt-2 text-sm text-amber-800">{exitPlateMsg}</div> : null}
          </Card>

          {overstayRows.length > 0 ? (
            <Card className="border-rose-200 bg-rose-50/60">
              <div className="text-sm font-semibold text-rose-900">Понаднормовий паркінг</div>
              <ul className="mt-2 list-inside list-disc text-sm text-rose-950">
                {overstayRows.map((r) => (
                  <li key={r.spot.id}>
                    Місце <span className="font-mono font-semibold">{r.spot.code}</span>
                    {r.vehicle ? (
                      <>
                        {" "}
                        — <span className="font-mono">{r.vehicle.plate_number}</span>
                      </>
                    ) : null}
                    {r.overstay_minutes != null ? <> — +{r.overstay_minutes} хв після кінця бронювання</> : null}
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          {loadError ? <div className="text-sm text-red-600">{loadError}</div> : null}

          <Card>
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="text-sm font-semibold text-zinc-900">Місця</div>
              <div className="flex flex-wrap gap-2 text-xs text-zinc-600">
                <span className="rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-0.5">вільне</span>
                <span className="rounded-lg border border-amber-200 bg-amber-50 px-2 py-0.5">заброньоване</span>
                <span className="rounded-lg border border-rose-200 bg-rose-50 px-2 py-0.5">зайняте</span>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
              {board.map((row) => (
                <button
                  key={row.spot.id}
                  type="button"
                  onClick={() => setModalRow(row)}
                  className={`rounded-2xl border p-3 text-left shadow-sm transition hover:opacity-95 ${spotTone(row.spot.status)}`}
                >
                  <div className="text-xs font-semibold uppercase tracking-wide opacity-70">{row.spot.status}</div>
                  <div className="mt-1 font-mono text-lg font-bold">{row.spot.code}</div>
                  {row.vehicle ? (
                    <div className="mt-1 truncate text-xs font-medium">{row.vehicle.plate_number}</div>
                  ) : (
                    <div className="mt-1 text-xs opacity-60">немає авто</div>
                  )}
                  {row.overstay_minutes != null && row.overstay_minutes > 0 ? (
                    <div className="mt-1 text-xs font-semibold text-rose-700">+{row.overstay_minutes} хв</div>
                  ) : null}
                </button>
              ))}
            </div>
          </Card>

          <Card>
            <div className="text-sm font-semibold text-zinc-900">Пошук авто за номером</div>
            <p className="mt-1 text-xs text-zinc-500">
              Окремий крок: знайдіть транспорт у каталозі за держномером. Реєстрація бронювання — у блоці нижче.
            </p>
            <div className="mt-4 max-w-xl">
              <div className="text-xs font-semibold text-zinc-500">Номерний знак</div>
              <div className="mt-1 flex flex-wrap gap-2">
                <Input
                  className="min-w-[200px] flex-1"
                  value={plateQuery}
                  onChange={(e) => onPlateInputChange(e.target.value)}
                  placeholder="AA1234BC"
                />
                <Button type="button" variant="secondary" disabled={busy} onClick={() => void searchPlate()}>
                  Знайти
                </Button>
              </div>
              {vehicles.length > 0 ? (
                <div className="mt-3 space-y-1">
                  <div className="text-xs font-semibold text-zinc-500">Результати</div>
                  {vehicles.map((v) => (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() => {
                        setSelectedVehicle(v);
                        setPlateQuery(v.plate_number);
                      }}
                      className={`block w-full rounded-xl border px-3 py-2 text-left text-sm ${
                        selectedVehicle?.id === v.id
                          ? "border-indigo-500 bg-indigo-50"
                          : "border-black/10 bg-white"
                      }`}
                    >
                      <span className="font-mono font-semibold">{v.plate_number}</span>
                      <span className="text-zinc-500"> — клієнт #{v.user_id}</span>
                      {(v.brand || v.model) && (
                        <span className="block text-xs text-zinc-600">
                          {[v.brand, v.model].filter(Boolean).join(" ")}
                          {v.color ? ` · ${v.color}` : ""}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              ) : null}
              {selectedVehicle ? (
                <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50/60 px-3 py-2 text-sm text-zinc-800">
                  <span className="font-semibold text-indigo-900">Обрано для бронювання:</span>{" "}
                  <span className="font-mono font-bold">{selectedVehicle.plate_number}</span>
                  <span className="text-zinc-600"> (клієнт #{selectedVehicle.user_id})</span>
                </div>
              ) : null}
              {plateSearchMsg ? <div className="mt-3 text-sm text-zinc-700">{plateSearchMsg}</div> : null}
            </div>
          </Card>

          <Card>
            <div className="text-sm font-semibold text-zinc-900">Реєстрація бронювання</div>
            <p className="mt-1 text-xs text-zinc-500">
              Обов’язково вкажіть номерний знак. Можна додатково скористатися блоком «Пошук авто за номером». Після
              створення — «Оплатити на місці» або оплата клієнтом у застосунку.
            </p>
            <div className="mt-4 grid max-w-xl gap-3">
              <label className="text-xs font-semibold text-zinc-500">
                Номерний знак авто
                <Input
                  className="mt-1 font-mono"
                  value={plateQuery}
                  onChange={(e) => onPlateInputChange(e.target.value)}
                  placeholder="AA1234BC"
                  autoComplete="off"
                />
              </label>
              {selectedVehicle &&
              normalizePlateLocal(plateQuery) === normalizePlateLocal(selectedVehicle.plate_number) ? (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 px-3 py-2 text-xs text-emerald-950">
                  Прив’язано до клієнта #{selectedVehicle.user_id}
                  {(selectedVehicle.brand || selectedVehicle.model) && (
                    <span className="block text-zinc-700">
                      {[selectedVehicle.brand, selectedVehicle.model].filter(Boolean).join(" ")}
                    </span>
                  )}
                </div>
              ) : null}
              <label className="text-xs font-semibold text-zinc-500">
                Вільне місце
                <select
                  className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-sm"
                  value={bookingSpotId === "" ? "" : String(bookingSpotId)}
                  onChange={(e) => setBookingSpotId(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="">—</option>
                  {freeSpots.map((r) => (
                    <option key={r.spot.id} value={r.spot.id}>
                      {r.spot.code}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs font-semibold text-zinc-500">
                Тариф
                <select
                  className="mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-sm"
                  value={bookingTariffId === "" ? "" : String(bookingTariffId)}
                  onChange={(e) => setBookingTariffId(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="">—</option>
                  {detail?.tariffs?.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.price_per_hour} UAH/h (#{t.id})
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs font-semibold text-zinc-500">
                Початок
                <Input type="datetime-local" value={plannedStart} onChange={(e) => setPlannedStart(e.target.value)} />
              </label>
              <label className="text-xs font-semibold text-zinc-500">
                Кінець
                <Input type="datetime-local" value={plannedEnd} onChange={(e) => setPlannedEnd(e.target.value)} />
              </label>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button type="button" disabled={busy} onClick={() => void submitBooking()}>
                Зареєструвати бронювання
              </Button>
              {lastCreated && lastCreated.status === "created" ? (
                <Button type="button" variant="secondary" disabled={busy} onClick={() => void payLastOr(lastCreated.id)}>
                  Оплатити бронювання #{lastCreated.id} (на місці)
                </Button>
              ) : null}
            </div>
            {bookingMsg ? <div className="mt-2 text-sm text-zinc-700">{bookingMsg}</div> : null}
          </Card>
        </>
      ) : null}

      <Modal open={modalRow !== null} title={modalRow ? `Місце ${modalRow.spot.code}` : ""} onClose={() => setModalRow(null)}>
        {modalRow ? (
          <div className="space-y-3 text-sm text-zinc-800">
            <div>
              <span className="text-zinc-500">Статус місця:</span>{" "}
              <span className="font-semibold">{modalRow.spot.status}</span>
            </div>
            {modalRow.vehicle ? (
              <div className="rounded-2xl border border-black/5 bg-zinc-50 p-3">
                <div className="text-xs font-semibold uppercase text-zinc-500">Авто</div>
                <div className="mt-1 font-mono text-lg font-bold">{modalRow.vehicle.plate_number}</div>
                <div className="text-xs text-zinc-600">
                  {[modalRow.vehicle.brand, modalRow.vehicle.model].filter(Boolean).join(" ") || "—"}
                  {modalRow.vehicle.color ? ` · ${modalRow.vehicle.color}` : ""}
                </div>
              </div>
            ) : null}
            {modalRow.booking ? (
              <div className="rounded-2xl border border-black/5 bg-white p-3">
                <div className="text-xs font-semibold uppercase text-zinc-500">Бронювання</div>
                <div className="mt-1 font-mono">#{modalRow.booking.id}</div>
                <div>Статус: {modalRow.booking.status}</div>
                <div className="text-xs text-zinc-600">
                  {new Date(modalRow.booking.planned_start_time).toLocaleString()} —{" "}
                  {new Date(modalRow.booking.planned_end_time).toLocaleString()}
                </div>
                {modalRow.booking.payments?.length ? (
                  <div className="mt-2 text-xs text-zinc-600">
                    Платежі:{" "}
                    {modalRow.booking.payments.map((p) => (
                      <span key={p.id} className="mr-2">
                        {p.amount} ({p.status})
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
            {modalRow.session ? (
              <div className="rounded-2xl border border-black/5 bg-white p-3">
                <div className="text-xs font-semibold uppercase text-zinc-500">Сесія</div>
                <div className="mt-1 font-mono">#{modalRow.session.id}</div>
                <div>В’їзд: {new Date(modalRow.session.entry_time).toLocaleString()}</div>
                <div>Статус: {modalRow.session.status}</div>
                {modalRow.overstay_minutes != null && modalRow.overstay_minutes > 0 ? (
                  <div className="mt-2 text-sm font-semibold text-rose-700">
                    Понаднормово на {modalRow.overstay_minutes} хв.
                  </div>
                ) : null}
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2 pt-2">
              {modalRow.booking?.status === "created" ? (
                <Button type="button" disabled={busy} onClick={() => void payLastOr(modalRow.booking!.id)}>
                  Позначити оплаченим
                </Button>
              ) : null}
              {modalRow.booking?.status === "paid" && !modalRow.session ? (
                <Button type="button" disabled={busy} onClick={() => void entryFromModal(modalRow)}>
                  Зареєструвати в’їзд
                </Button>
              ) : null}
              {modalRow.session?.status === "active" ? (
                <Button type="button" variant="secondary" disabled={busy} onClick={() => void exitFromModal(modalRow.session!.id)}>
                  Завершити сесію (виїзд)
                </Button>
              ) : null}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
