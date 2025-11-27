{{/*
Expand the name of the chart.
*/}}
{{- define "pylight.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "pylight.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "pylight.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "pylight.labels" -}}
helm.sh/chart: {{ include "pylight.chart" . }}
{{ include "pylight.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "pylight.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pylight.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "pylight.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "pylight.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate ConfigMap hash for pod restart on config change
*/}}
{{- define "pylight.configMapHash" -}}
{{- if .Values.config.createConfigMap }}
{{- if not .Values.config.existingConfigMap }}
{{- $config := .Values.config.inline }}
{{- if .Values.database.connectionString }}
{{- $dbConfig := dict "url" .Values.database.connectionString }}
{{- $config = merge (dict "database" $dbConfig) $config }}
{{- end }}
{{- $config | toYaml | sha256sum | trunc 8 }}
{{- else }}
{{- "existing" }}
{{- end }}
{{- else }}
{{- "existing" }}
{{- end }}
{{- end }}

{{/*
Generate Secret hash for pod restart on secret change
*/}}
{{- define "pylight.secretHash" -}}
{{- if .Values.database.createSecret }}
{{- if not .Values.database.existingSecret }}
{{- if .Values.database.connectionString }}
{{- .Values.database.connectionString | sha256sum | trunc 8 }}
{{- else }}
{{- "existing" }}
{{- end }}
{{- else }}
{{- "existing" }}
{{- end }}
{{- else }}
{{- "existing" }}
{{- end }}
{{- end }}

{{/*
Determine config file path based on configuration approach
*/}}
{{- define "pylight.configPath" -}}
{{- if .Values.config.existingConfigMap }}
{{- printf "/etc/pylight/%s" (.Values.config.key | default "config.yaml") }}
{{- else }}
{{- "/etc/pylight/config.yaml" }}
{{- end }}
{{- end }}

{{/*
Determine ConfigMap name (created vs existing)
*/}}
{{- define "pylight.configMapName" -}}
{{- if .Values.config.existingConfigMap }}
{{- .Values.config.existingConfigMap }}
{{- else }}
{{- printf "%s-configmap" (include "pylight.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Determine Secret name (created vs existing)
*/}}
{{- define "pylight.secretName" -}}
{{- if .Values.database.existingSecret }}
{{- .Values.database.existingSecret }}
{{- else }}
{{- printf "%s-secret" (include "pylight.fullname" .) }}
{{- end }}
{{- end }}

