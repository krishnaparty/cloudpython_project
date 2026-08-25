import { getToken, removeToken, saveToken } from "../auth/auth";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface ApiErrorResponse {
  detail?: string;
}

async function readResponseBody(
  response: Response,
): Promise<unknown> {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function loginUser(
  email: string,
  password: string,
): Promise<void> {
  /*
   * FastAPI OAuth2PasswordRequestForm username field expect karta hai.
   * Hum email ko username field mein send kar rahe hain.
   */
  const formData = new URLSearchParams();

  formData.set("username", email);
  formData.set("password", password);

  const response = await fetch(
    `${API_BASE_URL}/api/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
      body: formData,
    },
  );

  const body = await readResponseBody(response);

  if (!response.ok) {
    const errorBody = body as ApiErrorResponse;

    throw new Error(
      errorBody?.detail ?? "Login failed.",
    );
  }

  const loginResponse = body as LoginResponse;

  if (!loginResponse.access_token) {
    throw new Error(
      "Backend response mein access token nahi mila.",
    );
  }

  saveToken(loginResponse.access_token);
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  if (options.body && !headers.has("Content-Type")) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  const body = await readResponseBody(response);

  if (response.status === 401) {
    removeToken();
  }

  if (!response.ok) {
    const errorBody = body as ApiErrorResponse;

    throw new Error(
      errorBody?.detail ??
        `Request failed: ${response.status}`,
    );
  }

  return body as T;
}