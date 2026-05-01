export const delayByThrottle = (mode) => {
  switch (mode) {
    case "2g": return 2000;
    case "3g": return 800;
    case "4g": return 200;
    case "5g": return 50;
    default: return 0;
  }
};

export const runTests = (code, response) => {
  const results = [];

  const pm = {
    response: {
      code: response.status,
      json: () => JSON.parse(response.data)
    },
    test: (name, fn) => {
      try {
        fn();
        results.push({ name, status: "PASS" });
      } catch {
        results.push({ name, status: "FAIL" });
      }
    },
    expect: (val) => ({
      toBe: (exp) => {
        if (val !== exp) throw new Error();
      }
    })
  };

  try {
    eval(code);
  } catch (e) {
    results.push({ name: "Script Error", status: "FAIL" });
  }

  return results;
};

export const sendRequest = async ({
  url,
  method,
  headers,
  body,
  auth,
  throttle,
  tests
}) => {
  const finalHeaders = { ...headers };

  if (auth.type === "bearer") {
    finalHeaders["Authorization"] = `Bearer ${auth.token}`;
  }

  if (auth.type === "apiKey") {
    finalHeaders[auth.key] = auth.value;
  }

  const delay = delayByThrottle(throttle);
  if (delay) await new Promise((r) => setTimeout(r, delay));

  const start = performance.now();

  const res = await fetch(url, {
    method,
    headers: finalHeaders,
    body: method !== "GET" ? body : undefined
  });

  const text = await res.text();
  const time = Math.round(performance.now() - start);

  const result = {
    status: res.status,
    time,
    size: text.length,
    data: text
  };

  result.tests = runTests(tests, result);

  return result;
};