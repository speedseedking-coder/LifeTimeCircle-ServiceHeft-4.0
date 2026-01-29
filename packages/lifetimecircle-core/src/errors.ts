export class UnauthorizedError extends Error {
  public readonly code = "UNAUTHORIZED";
  constructor(message = "Nicht angemeldet.") {
    super(message);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends Error {
  public readonly code = "FORBIDDEN";
  constructor(message = "Keine Berechtigung.") {
    super(message);
    this.name = "ForbiddenError";
  }
}

export class BadRequestError extends Error {
  public readonly code = "BAD_REQUEST";
  constructor(message = "Ungültige Anfrage.") {
    super(message);
    this.name = "BadRequestError";
  }
}
