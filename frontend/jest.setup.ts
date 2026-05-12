import "@testing-library/jest-dom";

process.env.TZ = "UTC";
process.env.NEXT_PUBLIC_API_BASE_URL =
	process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

beforeEach(() => {
	jest.useRealTimers();
});

afterEach(() => {
	jest.clearAllTimers();
	window.localStorage.clear();
	window.sessionStorage.clear();
});
