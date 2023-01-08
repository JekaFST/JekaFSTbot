CREATE TABLE public.session_config (
    session_id          bigint, -- PRIMARY KEY
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
    sectors_to_close    integer,
    sectors_message_id  integer,
    locations           varchar,
    ll_message_ids      integer
--     CONSTRAINT
--     code        char(5) CONSTRAINT firstkey PRIMARY KEY,
--     title       varchar(40) NOT NULL,
--     did         integer NOT NULL,
--     date_prod   date,
--     kind        varchar(10),
--     len         interval hour to minute
)