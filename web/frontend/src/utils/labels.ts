export function formatExperimentContext(data: {
  id: string;
  name: string;
  domain?: string;
  instance?: string;
}) {
  const scope = data.domain && data.instance ? `${data.domain} / ${data.instance}` : undefined;
  return {
    id: data.id,
    name: data.name,
    scope,
    label: scope ? `${data.name} · ${scope}` : data.name,
    fullLabel: scope ? `${data.name} · ${scope} · ${data.id}` : `${data.name} · ${data.id}`,
  };
}

export function formatStudyContext(data: { id: string; name: string; instance_count?: number }) {
  return {
    id: data.id,
    name: data.name,
    label: data.name,
    fullLabel: `${data.name} · ${data.id}`,
    instanceCount: data.instance_count,
  };
}

export function formatRunContext(experimentId: string, runId: string, algorithm?: string) {
  const algo = algorithm ? ` · ${algorithm}` : "";
  return `${experimentId} · ${runId}${algo}`;
}

export function formatJobContext(job: {
  job_id: string;
  experiment_name?: string;
  config_path?: string;
  experiment_dir?: string;
  study_dir?: string;
}) {
  const target = job.experiment_dir ?? job.study_dir ?? "pending";
  const name = job.experiment_name ?? job.config_path ?? job.job_id;
  return {
    label: `${name} · ${target}`,
    fullLabel: `Job ${job.job_id} · ${name} · ${target}`,
  };
}
