export const MIN_PASSWORD_LENGTH = 8;

export function isNewPasswordValid(
  password: string,
  confirmation: string
): boolean {
  return password.length >= MIN_PASSWORD_LENGTH && password === confirmation;
}
