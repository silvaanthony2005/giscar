import { useState } from 'react'
import { Card } from '../atoms/Card'
import { Icon } from '../atoms/Icon'
import { SectionHeader } from '../molecules/SectionHeader'
import {
  attachmentUrl,
  useAttachments,
  useUploadAttachment,
} from '../entities/project/desarrollo-api'
import { descargar } from '../shared/api/client'

interface Props {
  /** Entidad dueña de los adjuntos (`plan`, `incidencia`, …). */
  tipo: string
  entidadId: string
  title?: string
  description?: string
}

/**
 * Panel de documentos y evidencia adjunta.
 * El servidor valida MIME, tamaño y tipo de entidad.
 */
export function AdjuntosPanel({
  tipo,
  entidadId,
  title = 'Documentos y evidencia',
  description = 'Archivos adjuntos de la entidad.',
}: Props) {
  const { data, error } = useAttachments(tipo, entidadId)
  const upload = useUploadAttachment()
  const [errDescarga, setErrDescarga] = useState<string | null>(null)
  const adjuntos = data ?? []

  return (
    <div>
      <SectionHeader icon="attach_file" title={title} description={description} />
      <Card className="p-space-lg">
        <ul className="space-y-space-sm">
          {adjuntos.map((a) => (
            <li key={a.id} className="flex items-center justify-between text-body-md">
              <span className="truncate text-on-surface">{a.nombre}</span>
              <button
                type="button"
                onClick={() =>
                  descargar(attachmentUrl(a.id)).catch((e: Error) => setErrDescarga(e.message))
                }
                className="ml-space-sm inline-flex shrink-0 items-center gap-1 text-secondary hover:underline"
              >
                <Icon name="download" size="sm" />
                Descargar
              </button>
            </li>
          ))}
          {adjuntos.length === 0 && (
            <li className="text-body-md text-on-surface-variant">Sin archivos adjuntos.</li>
          )}
        </ul>
        {/* El input nativo se oculta: su botón dice "Choose File" y el resto
            del sistema está en español. El <label> es el control visible. */}
        <label
          htmlFor={`adjunto-${tipo}-${entidadId}`}
          className="mt-space-lg inline-flex cursor-pointer items-center gap-space-sm rounded-lg bg-secondary-container px-space-md py-space-sm text-body-md font-medium text-on-secondary shadow-hairline transition-colors hover:bg-surface-container-high"
        >
          <Icon name="upload_file" size="sm" />
          Subir archivo (PDF, imagen, doc)
        </label>
        <input
          id={`adjunto-${tipo}-${entidadId}`}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.doc,.docx,.xls,.xlsx"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) upload.mutate({ tipo, entidadId, file })
            e.target.value = ''
          }}
          className="sr-only"
        />
        {upload.error && (
          <p className="mt-space-sm text-body-md text-on-error-container">
            {upload.error.message}
          </p>
        )}
        {errDescarga && (
          <p role="alert" className="mt-space-sm text-body-md text-on-error-container">
            {errDescarga}
          </p>
        )}
        {error && (
          <p className="mt-space-sm text-body-md text-on-error-container">{error.message}</p>
        )}
      </Card>
    </div>
  )
}
