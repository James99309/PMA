--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 16.8 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: user_event_subscriptions; Type: TABLE; Schema: public; Owner: nijie
--

CREATE TABLE public.user_event_subscriptions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    target_user_id integer NOT NULL,
    event_id integer NOT NULL,
    enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.user_event_subscriptions OWNER TO nijie;

--
-- Name: COLUMN user_event_subscriptions.user_id; Type: COMMENT; Schema: public; Owner: nijie
--

COMMENT ON COLUMN public.user_event_subscriptions.user_id IS '订阅者用户ID';


--
-- Name: COLUMN user_event_subscriptions.target_user_id; Type: COMMENT; Schema: public; Owner: nijie
--

COMMENT ON COLUMN public.user_event_subscriptions.target_user_id IS '被订阅的用户ID';


--
-- Name: COLUMN user_event_subscriptions.event_id; Type: COMMENT; Schema: public; Owner: nijie
--

COMMENT ON COLUMN public.user_event_subscriptions.event_id IS '事件ID';


--
-- Name: COLUMN user_event_subscriptions.enabled; Type: COMMENT; Schema: public; Owner: nijie
--

COMMENT ON COLUMN public.user_event_subscriptions.enabled IS '是否启用订阅';


--
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: nijie
--

CREATE SEQUENCE public.user_event_subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNER TO nijie;

--
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nijie
--

ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNED BY public.user_event_subscriptions.id;


--
-- Name: user_event_subscriptions id; Type: DEFAULT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.user_event_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.user_event_subscriptions_id_seq'::regclass);


--
-- Data for Name: user_event_subscriptions; Type: TABLE DATA; Schema: public; Owner: nijie
--

INSERT INTO public.user_event_subscriptions VALUES (21, 6, 6, 1, true, '2025-05-17 14:07:27.443121', '2025-05-17 14:07:27.443132');
INSERT INTO public.user_event_subscriptions VALUES (22, 6, 6, 2, true, '2025-05-17 14:07:27.443136', '2025-05-17 14:07:27.443139');
INSERT INTO public.user_event_subscriptions VALUES (23, 6, 6, 3, true, '2025-05-17 14:07:27.443146', '2025-05-17 14:07:27.443149');
INSERT INTO public.user_event_subscriptions VALUES (24, 6, 6, 4, true, '2025-05-17 14:07:27.443152', '2025-05-17 14:07:27.443154');


--
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nijie
--

SELECT pg_catalog.setval('public.user_event_subscriptions_id_seq', 24, true);


--
-- Name: user_event_subscriptions uq_user_target_event; Type: CONSTRAINT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT uq_user_target_event UNIQUE (user_id, target_user_id, event_id);


--
-- Name: user_event_subscriptions user_event_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: user_event_subscriptions user_event_subscriptions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.event_registry(id);


--
-- Name: user_event_subscriptions user_event_subscriptions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- Name: user_event_subscriptions user_event_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

