/**
 * Wasel on Cloudflare: one Worker in front of one Container.
 *
 *   /api/*, /webhook/*, /docs, /openapi.json  ->  the FastAPI container (a single named instance)
 *   everything else                            ->  static assets (the Next.js export in web/dist), served at the edge
 *
 * The container's disk is ephemeral. The SQLite file is restored from, and saved to, an R2 bucket through the
 * outbound handler below: the container calls http://state.wasel.internal/snapshot, the Worker answers from the STATE
 * binding, and no Cloudflare credential ever enters the container. See docs/operations/cloudflare.md.
 */
import { Container, getContainer } from "@cloudflare/containers";
import containerEnv from "../../container-env.json";
import { handleSnapshot } from "./snapshot.ts";

// required by the outbound interception below (the container reaches the R2 snapshot through it)
export { ContainerProxy } from "@cloudflare/containers";

const SNAPSHOT_HOST = "state.wasel.internal";
const MAX_REQUEST_BYTES = 1024 * 1024; // the container refuses more (64 KB, 1 MiB for the webhook); do not wake it for it
const BACKEND_PATHS = ["/api/", "/webhook/", "/docs", "/openapi.json"];

type Env = Cloudflare.Env & Record<string, string | undefined>;

function json(status: number, code: string, message: string): Response {
  return Response.json({ error: { code, message } }, { status, headers: { "Cache-Control": "no-store" } });
}

export function isBackendPath(pathname: string): boolean {
  return BACKEND_PATHS.some((p) => (p.endsWith("/") ? pathname.startsWith(p) : pathname === p || pathname.startsWith(p + "/")));
}

/** Name -> value for the variables and secrets the container may see. Unset names are left out. */
export function containerEnvFrom(env: Record<string, unknown>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const name of [...containerEnv.vars, ...containerEnv.secrets]) {
    const v = env[name];
    if (typeof v === "string") out[name] = v;
  }
  return out;
}

export class WaselContainer extends Container<Env> {
  defaultPort = 8000;
  enableInternet = true; // Groq / Gemini / the WhatsApp Graph API
  pingEndpoint = "wasel/api/health";
  sleepAfter: string | number = "15m";

  static outboundByHost = { [SNAPSHOT_HOST]: (req: Request, env: Env) => handleSnapshot(req, env.STATE) };

  constructor(ctx: ConstructorParameters<typeof Container<Env>>[0], env: Env) {
    super(ctx, env);
    this.sleepAfter = env.CONTAINER_SLEEP_AFTER ?? "15m";
    this.envVars = containerEnvFrom(env);
  }

  override onStop(params: unknown) {
    console.log("wasel container stopped", JSON.stringify(params));
  }

  override onError(error: unknown) {
    console.error("wasel container error", error);
  }
}

function backend(env: Env) {
  // one instance: the SQLite file and the 1 s worker loop are singletons
  return getContainer(env.WASEL, "primary");
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { pathname } = new URL(request.url);
    if (!isBackendPath(pathname)) return env.ASSETS.fetch(request);
    const len = request.headers.get("content-length");
    if (len && Number(len) > MAX_REQUEST_BYTES) return json(413, "PAYLOAD_TOO_LARGE", "body over 1 MiB");
    try {
      return await backend(env).fetch(request);
    } catch (e) {
      console.error("backend unavailable", e);
      return json(503, "BACKEND_UNAVAILABLE", "the backend is starting or unavailable; retry shortly");
    }
  },

  // Cron: keeps the container awake outside public mode, where no-reply timeouts must fire while nobody browses.
  // In public mode (a demo) it does nothing, so the container sleeps when idle.
  async scheduled(_event: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    if ((env.APP_MODE ?? "public") === "public") return;
    ctx.waitUntil(backend(env).fetch(new Request("http://wasel/api/health")).then((r) => r.body?.cancel()));
  },
} satisfies ExportedHandler<Env>;
