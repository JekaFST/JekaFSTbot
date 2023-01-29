CREATE TABLE public.session_config (
    session_id          bigint PRIMARY KEY,
    active              boolean,
    login               varchar,
    password            varchar,
    en_domain           varchar,
    game_id             varchar,
    channel_name        varchar,
    cookie              varchar,
    game_url            varchar,
    login_url           varchar,
    game_model_status   varchar,
    use_channel         boolean,
    stop_updater        boolean,
    put_updater_task    boolean,
    delay               integer,
    send_codes          boolean,
    storm_game          boolean,
    curr_level_id       integer,
    sectors_to_close    varchar,
    sectors_message_id  bigint,
    locations           jsonb,
    ll_message_ids      jsonb
);


CREATE TABLE public.additional_chats(
    add_chat_id         bigint PRIMARY KEY,
    session_id          bigint NOT NULL
);

CREATE TABLE public.bot_tokens (
    bot_token           varchar PRIMARY KEY,
    type                varchar NOT NULL,
    number              integer
    -- CONTRAINT type main value - unique
    -- main bot token = 370362982:AAH5ojKT0LSw8jS-vLfDF1bDE8rWWDyTeso
);

CREATE TABLE public.tags_to_cut (
    tags_to_cut         varchar PRIMARY KEY
);