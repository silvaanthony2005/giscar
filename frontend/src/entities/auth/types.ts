export type Departamento = 'ventas' | 'desarrollo' | 'despacho' | 'tecnologia' | 'rrhh'

export type Rol = 'admin' | 'usuario'

export interface User {
  id: string
  email: string
  nombre: string
  documento: string | null
  telefono: string | null
  direccion: string | null
  cargo: string | null
  departamento: Departamento
  estado: 'activo' | 'bloqueado'
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}
