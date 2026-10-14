import { api } from '../../shared/api/client'
import type { LoginResponse, User } from './types'

export async function login(email: string, password: string): Promise<LoginResponse> {
  return api.post<LoginResponse>('/auth/login', { email, password })
}

export async function fetchMe(): Promise<User> {
  return api.get<User>('/auth/me')
}
