CREATE TABLE public.session_config (
    session_id              bigint PRIMARY KEY,
    active                  boolean,
    login                   varchar,
    password                varchar,
    en_domain               varchar,
    game_id                 varchar,
    channel_name            varchar,
    cookie                  varchar,
    game_url                varchar,
    login_url               varchar,
    game_model_status       varchar,
    use_channel             boolean,
    stop_updater            boolean,
    put_updater_task        boolean,
    delay                   integer,
    send_codes              boolean,
    storm_game              boolean,
    curr_level_id           integer,
    sectors_to_close        varchar,
    sectors_message_id      bigint,
    locations               jsonb,
    ll_message_ids          jsonb
);


CREATE TABLE public.additional_chats(
    add_chat_id             bigint PRIMARY KEY,
    session_id              bigint NOT NULL
);

CREATE TABLE public.bot_tokens (
    bot_token               varchar PRIMARY KEY,
    type                    varchar NOT NULL,
    number                  integer
    -- CONTRAINT type main value - unique
    -- main bot token = 370362982:AAH5ojKT0LSw8jS-vLfDF1bDE8rWWDyTeso
);

CREATE TABLE public.tags_to_cut (
    tags_to_cut             varchar PRIMARY KEY
);

CREATE TABLE public.levels (
    session_id              bigint,
    level_id                integer,
    game_id                 varchar,
    number                  integer,
    is_passed               boolean,
    dismissed               boolean,
    time_to_up_sent         boolean,
    level_name              varchar
    -- CONSTRAINT session_id & level_id unique
);

CREATE TABLE public.helps (
    session_id              bigint,
    hint_id                 integer,
    game_id                 varchar,
    not_sent                boolean,
    time_not_sent           boolean
    -- CONSTRAINT session_id & hint_id unique
);

CREATE TABLE public.pen_helps (
    session_id              bigint,
    pen_hint_id             integer,
    game_id                 varchar,
    not_sent                boolean
    -- CONSTRAINT session_id & hint_id unique
);

CREATE TABLE public.bonuses (
    session_id              bigint,
    bonus_id                integer,
    game_id                 varchar,
    info_not_sent           boolean,
    award_not_sent          boolean,
    level_id                integer,
    code                    varchar,
    bonus_name              varchar,
    bonus_number            integer,
    player                  varchar
    -- CONSTRAINT session_id & hint_id unique
);

CREATE TABLE public.sectors (
    session_id              bigint,
    sector_id               integer,
    game_id                 varchar,
    answer_info_not_sent    boolean,
    code                    varchar,
    level_id                integer,
    sector_name             varchar,
    sector_order            integer,
    player                  varchar
    -- CONSTRAINT session_id & hint_id unique
);

CREATE TABLE public.messages (
    session_id              bigint,
    message_id              integer,
    game_id                 varchar,
    message_not_sent        boolean,
    -- CONSTRAINT session_id & hint_id unique
);
