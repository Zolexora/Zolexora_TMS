export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly info?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
