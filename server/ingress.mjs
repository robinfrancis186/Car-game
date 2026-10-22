/** Bounded single-process public-alpha ingress. Origin checks are NOT authentication. */
import {performance} from 'node:perf_hooks';

export function bucket(capacity, perSecond, now = () => performance.now()) {
  let available = capacity, previous = now();
  return () => {
    const current = now();
    available = Math.min(capacity, available + Math.max(0, current - previous) * perSecond / 1000);
    previous = current;
    if (available < 1) return false;
    available--;
    return true;
  };
}

export function ingress(options = {}) {
  const publicMode = options.publicOrigin !== undefined;
  let origin, hostname;
  if (publicMode) {
    const url = new URL(options.publicOrigin);
    if (url.protocol !== 'https:' || url.username || url.password || url.port ||
        url.pathname !== '/' || url.search || url.hash || url.origin !== options.publicOrigin) {
      throw new Error('Public origin must be one exact HTTPS origin, with no path or credentials');
    }
    origin = url.origin; hostname = url.hostname;
    if (options.host && options.host !== '0.0.0.0') throw new Error('Public alpha binds 0.0.0.0');
  } else if (options.host && options.host !== '127.0.0.1') {
    throw new Error('Local alpha only binds 127.0.0.1');
  }
  return {
    publicMode, origin, host: publicMode ? '0.0.0.0' : '127.0.0.1',
    maxRooms: publicMode ? 1 : 8,
    maxClients: publicMode ? 6 : 32,
    httpBudget: bucket(120, 2), upgradeBudget: bucket(16, 1),
    createBudget: bucket(6, 0.1), messageBudget: bucket(500, 250),
    validHost(host, port) { return publicMode ? host === hostname : [`127.0.0.1:${port}`, `localhost:${port}`].includes(host); },
    validOrigin(value, port) { return publicMode ? value === origin : !value || [`http://127.0.0.1:${port}`, `http://localhost:${port}`].includes(value); },
  };
}

export function renderOptions(env = process.env) {
  const port = Number(env.PORT || 8787);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Invalid PORT');
  if (env.PUBLIC_ALPHA !== 'true') return {port};
  if (env.RENDER !== 'true' || !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.onrender\.com$/.test(env.RENDER_EXTERNAL_HOSTNAME || '') ||
      !env.PORT || port < 1 || [18012, 18013, 19099].includes(port)) {
    throw new Error('Public mode requires Render-provided hostname and PORT');
  }
  return {port, publicOrigin: `https://${env.RENDER_EXTERNAL_HOSTNAME}`};
}
