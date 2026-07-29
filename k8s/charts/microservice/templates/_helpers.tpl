{{/* 
    Nombre base de la app 
*/}}
{{- define "microservice.name" -}}
{{- default .Chart.Name .Values.app.name | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
    Create chart name and version as used by the chart label.
*/}}
{{- define "microservice.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
    Common labels
*/}}
{{- define "microservice.labels" -}}
helm.sh/chart: {{ include "microservice.chart" . }}
{{ include "microservice.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
env: {{ .Values.env }}
{{- end }}


{{/*
    Selector labels
*/}}
{{- define "microservice.selectorLabels" -}}
app.kubernetes.io/name: {{ include "microservice.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* 
    envFrom compartido: configmaps + secrets desde values */}}
{{- define "microservice.envFrom" -}}
{{- range .Values.app.configMaps }}
- configMapRef:
    name: {{ . }}
{{- end }}
{{- range .Values.app.secrets }}
- secretRef:
    name: {{ . }}
{{- end }}
{{- end }}


{{/*
    DATABASE_URL desde el secret generado por cnpg (<app>-cluster-app)
*/}}
{{- define "microservice.dbEnv" -}}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: "{{ .Values.app.name }}-cluster-app"
      key: uri
{{- end }}

{{/*
    data del ConfigMap: itera el MAPA .Values.config → "KEY: valor"
    (range sobre mapa: Helm ordena las claves alfabéticamente → hash estable)
*/}}
{{- define "microservice.configData" -}}
{{- range $key, $value := .Values.config }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}