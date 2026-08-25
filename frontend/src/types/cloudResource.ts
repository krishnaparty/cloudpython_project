export interface CloudResource {
  id: number;

  aws_account_id: string;
  resource_id: string;
  resource_type: string;
  region: string;

  name: string | null;
  availability_zone: string | null;
  instance_type: string | null;
  state: string | null;
  launch_time: string | null;

  owner_email: string | null;
  project_name: string | null;
  environment: string | null;

  is_compliant: boolean;
  missing_tags: string[] | null;
  tags: Record<string, string> | null;

  first_seen_at: string;
  last_synced_at: string;
}