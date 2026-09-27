// Get API URL from environment variable
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
    ? "http://localhost:8000" 
    : '');

// Check for placeholder URLs
if (typeof window !== 'undefined' && BASE_URL && BASE_URL.includes('your-railway-url')) {
  console.error(
    '❌ NEXT_PUBLIC_API_URL contains placeholder value! ' +
    'Please update it in Vercel environment variables to your actual Railway backend URL.'
  );
}

const API_BASE = BASE_URL ? `${BASE_URL}/api/v1` : '/api/v1';
const LEVELS = ["debug", "info", "warning", "error", "critical"] as const;
export type LogLevel = (typeof LEVELS)[number];

// The COD Risk backend has no diagnostics endpoint: log in the browser only.
async function postDiagnostics(path: string, payload: Record<string, any>) {
  console.warn(`[diagnostics] ${path}`, payload);
}

export async function logClientError(
  message: string,
  options?: {
    level?: LogLevel;
    stack?: string;
    component?: string;
    url?: string;
    metadata?: Record<string, any>;
    userId?: string | null;
    tenantId?: string | null;
  }
) {
  await postDiagnostics("frontend-error", {
    message,
    level: options?.level || "error",
    stack: options?.stack,
    component: options?.component,
    url: options?.url || (typeof window !== "undefined" ? window.location.href : undefined),
    metadata: options?.metadata || {},
    user_id: options?.userId || undefined,
    tenant_id: options?.tenantId || undefined,
  });
}

export async function logUserAction(
  action: string,
  data?: Record<string, any>,
  options?: { userId?: string | null; tenantId?: string | null; success?: boolean }
) {
  await postDiagnostics("frontend-action", {
    action,
    data: data || {},
    user_id: options?.userId || undefined,
    tenant_id: options?.tenantId || undefined,
    success: options?.success ?? true,
  });
}

export async function trackPerformance(
  metric: string,
  duration: number,
  options?: { userId?: string | null; tenantId?: string | null; metadata?: Record<string, any> }
) {
  await postDiagnostics("frontend-performance", {
    metric,
    duration_ms: duration,
    user_id: options?.userId || undefined,
    tenant_id: options?.tenantId || undefined,
    metadata: options?.metadata || {},
  });
}

/**
 * Enhanced fetch wrapper with diagnostics
 */
export async function fetchWithLogging(
  url: string,
  options?: RequestInit
): Promise<Response> {
  const startTime = typeof performance !== "undefined" ? performance.now() : Date.now();

  try {
    const response = await fetch(url, options);
    const duration = (typeof performance !== "undefined" ? performance.now() : Date.now()) - startTime;

    if (duration > 2000) {
      trackPerformance("slow_api_call", duration, {
        metadata: { url, method: options?.method || "GET" },
      });
    }

    if (!response.ok) {
      const preview = await response.clone().text();
      await logClientError(`API Error: ${response.status} ${response.statusText}`, {
        level: "error",
        metadata: {
          url,
          method: options?.method || "GET",
          status: response.status,
          responseBody: preview.substring(0, 1000),
        },
      });
    }

    return response;
  } catch (error) {
    const duration = (typeof performance !== "undefined" ? performance.now() : Date.now()) - startTime;
    await logClientError(error instanceof Error ? error.message : "Unknown fetch error", {
      level: "critical",
      stack: error instanceof Error ? error.stack : undefined,
      metadata: {
        url,
        method: options?.method || "GET",
        duration,
      },
    });
    throw error;
  }
}

export async function authenticatedFetch(
  url: string,
  options?: RequestInit
): Promise<Response> {
  if (typeof window === "undefined") {
    throw new Error("authenticatedFetch can only run in the browser");
  }

  const token = window.localStorage.getItem("access_token");
  
  if (!token) {
    await logClientError("Missing authentication token", {
      level: "warning",
      metadata: { url },
    });
    throw new Error("Authentication required");
  }

  const headers = new Headers(options?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Content-Type", "application/json");

  return fetchWithLogging(url, {
    ...options,
    headers,
  });
}

export async function parseJsonResponse<T>(response: Response): Promise<T> {
  try {
    return await response.json();
  } catch (error) {
    await logClientError("Failed to parse JSON response", {
      level: "error",
      metadata: {
        url: response.url,
        status: response.status,
        statusText: response.statusText,
      },
      stack: error instanceof Error ? error.stack : undefined,
    });
    throw new Error("Failed to parse JSON response");
  }
}
