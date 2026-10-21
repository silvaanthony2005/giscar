import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '../entities/auth/store'
import { LoginPage } from '../pages/auth/LoginPage'
import { DetalleProyectoDesarrolloPage } from '../pages/desarrollo/DetalleProyectoDesarrolloPage'
import { ProyectosDesarrolloPage } from '../pages/desarrollo/ProyectosDesarrolloPage'
import { ColaDespachoPage } from '../pages/despacho/ColaDespachoPage'
import { DetalleDespachoPage } from '../pages/despacho/DetalleDespachoPage'
import { ActividadRRHHPage } from '../pages/rrhh/ActividadRRHHPage'
import { DashboardRRHHPage } from '../pages/rrhh/DashboardRRHHPage'
import { ProyectosRRHHPage } from '../pages/rrhh/ProyectosRRHHPage'
import { UsuariosRRHHPage } from '../pages/rrhh/UsuariosRRHHPage'
import { ColaIncidenciasPage } from '../pages/tecnologia/ColaIncidenciasPage'
import { DetalleIncidenciaPage } from '../pages/tecnologia/DetalleIncidenciaPage'
import { ReportarIncidenciaPage } from '../pages/incidencias/ReportarIncidenciaPage'
import { ClientesPage } from '../pages/ventas/ClientesPage'
import { DetalleProyectoVentasPage } from '../pages/ventas/DetalleProyectoVentasPage'
import { ProyectosVentasPage } from '../pages/ventas/ProyectosVentasPage'
import { DashboardLayout } from '../templates/DashboardLayout'
import { ProtectedRoute } from './ProtectedRoute'

export function App() {
  const token = useAuthStore((s) => s.token)

  if (!token) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Navigate to="/panel" replace />} />
          <Route path="/panel" element={<PanelRedirect />} />

          <Route path="/ventas" element={<ProyectosVentasPage />} />
          <Route path="/ventas/clientes" element={<ClientesPage />} />
          <Route path="/ventas/proyectos/:id" element={<DetalleProyectoVentasPage />} />

          <Route path="/desarrollo" element={<ProyectosDesarrolloPage />} />
          <Route path="/desarrollo/proyectos/:id" element={<DetalleProyectoDesarrolloPage />} />

          <Route path="/despacho" element={<ColaDespachoPage />} />
          <Route path="/despacho/proyectos/:id" element={<DetalleDespachoPage />} />

          <Route path="/tecnologia" element={<ColaIncidenciasPage />} />
          <Route path="/tecnologia/incidencias/:id" element={<DetalleIncidenciaPage />} />
          <Route path="/incidencias/nueva" element={<ReportarIncidenciaPage />} />

          <Route path="/rrhh" element={<DashboardRRHHPage />} />
          <Route path="/rrhh/usuarios" element={<UsuariosRRHHPage />} />
          <Route path="/rrhh/proyectos" element={<ProyectosRRHHPage />} />
          <Route path="/rrhh/actividad" element={<ActividadRRHHPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function PanelRedirect() {
  const user = useAuthStore((s) => s.user)
  // Ruta de inicio de cada módulo (configuración de navegación, no negocio).
  const inicio: Record<string, string> = {
    ventas: '/ventas',
    desarrollo: '/desarrollo',
    despacho: '/despacho',
    tecnologia: '/tecnologia',
    rrhh: '/rrhh',
  }
  return <Navigate to={inicio[user?.departamento ?? ''] ?? '/login'} replace />
}
