-- Supabase PostgreSQL Schema for Security & Management Bot
-- Run this in Supabase SQL Editor if creating tables manually

CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    prefix VARCHAR(10) DEFAULT '!',
    language VARCHAR(10) DEFAULT 'ar',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS security_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    anti_raid_enabled BOOLEAN DEFAULT FALSE,
    anti_raid_join_threshold INT DEFAULT 5,
    anti_raid_time_window INT DEFAULT 10,
    anti_raid_action VARCHAR(50) DEFAULT 'lockdown', -- lockdown, kick, ban, timeout
    anti_nuke_enabled BOOLEAN DEFAULT FALSE,
    anti_nuke_channel_threshold INT DEFAULT 3,
    anti_nuke_role_threshold INT DEFAULT 3,
    anti_nuke_time_window INT DEFAULT 10,
    anti_nuke_action VARCHAR(50) DEFAULT 'remove_roles', -- remove_roles, ban, timeout
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS automod_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT FALSE,
    anti_spam_enabled BOOLEAN DEFAULT TRUE,
    max_messages_per_5s INT DEFAULT 5,
    max_mentions INT DEFAULT 5,
    block_invites BOOLEAN DEFAULT TRUE,
    block_links BOOLEAN DEFAULT FALSE,
    bad_words TEXT[] DEFAULT '{}',
    whitelisted_words TEXT[] DEFAULT '{}',
    whitelisted_links TEXT[] DEFAULT '{}',
    ignored_channels BIGINT[] DEFAULT '{}',
    ignored_roles BIGINT[] DEFAULT '{}',
    action VARCHAR(50) DEFAULT 'delete_and_warn',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT FALSE,
    channel_id BIGINT,
    verified_role_id BIGINT,
    unverified_role_id BIGINT,
    panel_message_id BIGINT,
    title VARCHAR(255) DEFAULT 'نظام التحقق - Verification System',
    description TEXT DEFAULT 'اضغط على الزر أدناه لإكمال عملية التحقق والحصول على الرتبة.',
    button_text VARCHAR(100) DEFAULT 'تحقق الآن / Verify',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS log_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    member_log_channel_id BIGINT,
    message_log_channel_id BIGINT,
    moderation_log_channel_id BIGINT,
    role_log_channel_id BIGINT,
    channel_log_channel_id BIGINT,
    server_log_channel_id BIGINT,
    security_log_channel_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS punishment_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    warn_3_action VARCHAR(50) DEFAULT 'timeout_1h',
    warn_5_action VARCHAR(50) DEFAULT 'kick',
    warn_7_action VARCHAR(50) DEFAULT 'ban',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warning_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    issuer_role_id BIGINT,
    viewer_role_id BIGINT,
    editor_role_id BIGINT,
    remover_role_id BIGINT,
    expirer_role_id BIGINT,
    evidence_manager_role_id BIGINT,
    settings_manager_role_id BIGINT,
    evidence_channel_id BIGINT,
    default_warning_duration VARCHAR(50) DEFAULT '30d',
    staff_demotion_enabled BOOLEAN DEFAULT TRUE,
    staff_demotion_threshold INT DEFAULT 3,
    demotion_action VARCHAR(50) DEFAULT 'remove_roles',
    verbal_warning_threshold INT DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warnings (
    warning_id VARCHAR(36) PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    warning_type VARCHAR(20) DEFAULT 'formal' NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    reason TEXT NOT NULL,
    evidence_url TEXT,
    duration_seconds BIGINT,
    expires_at TIMESTAMP WITH TIME ZONE,
    edited_by BIGINT,
    edit_history TEXT,
    removed_by BIGINT,
    removal_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warning_evidence (
    evidence_id VARCHAR(36) PRIMARY KEY,
    warning_id VARCHAR(36) NOT NULL REFERENCES warnings(warning_id) ON DELETE CASCADE,
    uploaded_by BIGINT NOT NULL,
    content_url TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voice_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    voice_manager_role_id BIGINT,
    voice_log_channel_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voice_action_logs (
    log_id VARCHAR(36) PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
    executor_id BIGINT NOT NULL,
    target_id BIGINT,
    action_type VARCHAR(50) NOT NULL,
    channel_id BIGINT,
    target_channel_id BIGINT,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_actions (
    action_id VARCHAR(36) PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- warn, timeout, kick, ban, unban, softban, purge, lock, unlock
    reason TEXT,
    duration INT, -- in seconds if applicable
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS whitelist_users (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    added_by BIGINT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS whitelist_roles (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL,
    added_by BIGINT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, role_id)
);

CREATE TABLE IF NOT EXISTS whitelist_bots (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
    bot_id BIGINT NOT NULL,
    added_by BIGINT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, bot_id)
);

CREATE TABLE IF NOT EXISTS command_shortcuts (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds(guild_id) ON DELETE CASCADE,
    trigger_word VARCHAR(100) NOT NULL,
    target_action VARCHAR(50) NOT NULL,
    allowed_roles VARCHAR(500),
    ignored_roles VARCHAR(500),
    allowed_users VARCHAR(500),
    allowed_channels VARCHAR(500),
    ignored_channels VARCHAR(500),
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_guild_trigger_word UNIQUE (guild_id, trigger_word)
);

-- INDEXES FOR MAXIMUM QUERY PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_warnings_guild_user ON warnings(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_mod_actions_guild ON moderation_actions(guild_id);
CREATE INDEX IF NOT EXISTS idx_whitelist_users_guild ON whitelist_users(guild_id);
CREATE INDEX IF NOT EXISTS idx_whitelist_roles_guild ON whitelist_roles(guild_id);
CREATE INDEX IF NOT EXISTS idx_whitelist_bots_guild ON whitelist_bots(guild_id);
CREATE INDEX IF NOT EXISTS idx_shortcuts_guild ON command_shortcuts(guild_id);
CREATE INDEX IF NOT EXISTS idx_shortcuts_trigger ON command_shortcuts(trigger_word);
