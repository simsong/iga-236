/// <reference lib="webworker" />
import * as openpgp from "openpgp";

type InMsg =
  | { type: "start"; armored: string; passwords: string[] }
  | { type: "stop" };

type OutMsg =
  | { type: "testing"; index: number }
  | { type: "result"; index: number; ok: boolean; message?: string; email?: string }
  | { type: "done"; found: boolean; index?: number }
  | { type: "error"; message: string };

let abort = false;

self.onmessage = async (ev: MessageEvent<InMsg>) => {
  const msg = ev.data;
  if (msg.type === "stop") { abort = true; return; }
  if (msg.type !== "start") return;

  abort = false;

  try {
    const message = await openpgp.readMessage({ armoredMessage: msg.armored });

    const passwords = msg.passwords;
    let found = false;

    for (let i = 0; i < passwords.length; i++) {
      if (abort) break;

      const pw = passwords[i];

      // Inform UI which index is being tested
      post({ type: "testing", index: i });

      let ok = false;
      let meta: { message?: string; email?: string } = {};

      try {
        const res = await openpgp.decrypt({
          message,
          passwords: [pw],
          format: "utf8",
        });
        const data = typeof res.data === "string" ? res.data : "";
        const parsed = parseDecrypted(data);
        if (parsed && parsed.password === pw) {
          ok = true;
          meta = { message: parsed.message, email: parsed.email };
        }
      } catch {
        ok = false;
      }

      post({ type: "result", index: i, ok, ...meta });

      if (ok) {
        found = true;
        break;
      }

      // Yield to let the event loop breathe (prevents long-tasks)
      if (i % 250 === 0) await microYield();
    }

    post({ type: "done", found });
  } catch (e: any) {
    post({ type: "error", message: String(e?.message || e) });
  }
};

function post(m: OutMsg) { (self as any).postMessage(m); }
function microYield() { return new Promise<void>(r => setTimeout(r, 0)); }

/** Expect:
 *  message: <...>
 *  email: <student email>
 *  password: <the decrypt password>
 */
function parseDecrypted(plain: string): { message: string; email: string; password: string } | null {
  const lines = plain.split(/\r?\n/).map(l => l.trim());
  let msg = "", email = "", pw = "";
  for (const l of lines) {
    const m = l.match(/^message:\s*(.*)$/i);
    if (m) { msg = m[1]; continue; }
    const e = l.match(/^email:\s*(.*)$/i);
    if (e) { email = e[1]; continue; }
    const p = l.match(/^password:\s*(.*)$/i);
    if (p) { pw = p[1]; continue; }
  }
  if (!msg || !email || !pw) return null;
  return { message: msg, email, password: pw };
}
