export type CinematicRouteTone = "opening" | "mission" | "battle" | "briefing" | "world" | "finale";
export type CinematicRoutePage = "home" | "dashboard" | "simulations" | "reports" | "projects" | "visualization" | "admin" | "auth" | "default";

export function getRouteTone(pathname: string): CinematicRouteTone {
  if (pathname.startsWith("/auth")) {
    return "opening";
  }

  if (pathname.startsWith("/about")) {
    return "briefing";
  }

  if (pathname.startsWith("/expertise")) {
    return "mission";
  }

  if (pathname.startsWith("/credibility")) {
    return "finale";
  }

  if (pathname.startsWith("/simulations")) {
    return "battle";
  }

  if (pathname.startsWith("/visualization/mission-control")) {
    return "battle";
  }

  if (pathname.startsWith("/reports")) {
    return "briefing";
  }

  if (pathname.startsWith("/visualization/global-risk-atlas")) {
    return "world";
  }

  if (pathname.startsWith("/admin/governance")) {
    return "finale";
  }

  if (pathname.startsWith("/dashboard")) {
    return "mission";
  }

  return "mission";
}

export function getRoutePage(pathname: string): CinematicRoutePage {
  if (pathname === "/") {
    return "home";
  }

  if (pathname.startsWith("/about")) {
    return "home";
  }

  if (pathname.startsWith("/expertise")) {
    return "home";
  }

  if (pathname.startsWith("/credibility")) {
    return "home";
  }

  if (pathname.startsWith("/dashboard")) {
    return "dashboard";
  }

  if (pathname.startsWith("/simulations")) {
    return "simulations";
  }

  if (pathname.startsWith("/reports")) {
    return "reports";
  }

  if (pathname.startsWith("/projects")) {
    return "projects";
  }

  if (pathname.startsWith("/visualization")) {
    return "visualization";
  }

  if (pathname.startsWith("/admin")) {
    return "admin";
  }

  if (pathname.startsWith("/auth")) {
    return "auth";
  }

  return "default";
}
