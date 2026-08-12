export interface BotStatus {
  configured: boolean;
  hasToken: boolean;
  hasDb: boolean;
  databaseUrl: string;
  environment: string;
  pythonVersion: string;
  botVersion: string;
  architecture: string;
}

export interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  children?: FileItem[];
}

export interface CommandInfo {
  name: string;
  category: 'security' | 'automod' | 'moderation' | 'warnings' | 'voice' | 'verification' | 'logs' | 'whitelist' | 'utility';
  description: string;
  permission: string;
  syntax: string;
  options: { name: string; description: string; required: boolean }[];
}
