const CALENDLY_HOST = "calendly.com";
const BROKEN_SLUG = "request-demo";

export function normalizeDemoBookingUrl(url: string): string {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.toLowerCase() !== CALENDLY_HOST) {
      return url;
    }

    const segments = parsed.pathname.split("/").filter(Boolean);
    if (segments.length >= 2 && segments[segments.length - 1].toLowerCase() === BROKEN_SLUG) {
      parsed.pathname = `/${segments.slice(0, -1).join("/")}`;
      parsed.search = "";
      parsed.hash = "";
      return parsed.toString();
    }

    return parsed.toString();
  } catch {
    return url;
  }
}