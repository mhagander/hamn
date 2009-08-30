--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: planet; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA planet;


SET search_path = planet, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: aggregatorlog; Type: TABLE; Schema: planet; Owner: -; Tablespace: 
--

CREATE TABLE aggregatorlog (
    id integer NOT NULL,
    ts timestamp with time zone DEFAULT now() NOT NULL,
    feed integer NOT NULL,
    success boolean NOT NULL,
    info text NOT NULL
);


--
-- Name: feeds; Type: TABLE; Schema: planet; Owner: -; Tablespace: 
--

CREATE TABLE feeds (
    id integer NOT NULL,
    feedurl text,
    name text,
    blogurl text DEFAULT ''::text NOT NULL,
    lastget timestamp with time zone DEFAULT '2000-01-01 00:00:00+00'::timestamp with time zone NOT NULL,
    userid text,
    approved boolean DEFAULT false NOT NULL,
    authorfilter text DEFAULT ''::text NOT NULL
);


--
-- Name: posts; Type: TABLE; Schema: planet; Owner: -; Tablespace: 
--

CREATE TABLE posts (
    id integer NOT NULL,
    feed integer NOT NULL,
    guid text,
    link text,
    txt text,
    dat timestamp with time zone NOT NULL,
    title text NOT NULL,
    guidisperma boolean NOT NULL,
    hidden boolean DEFAULT false NOT NULL,
    twittered boolean DEFAULT false NOT NULL,
    shortlink text
);


--
-- Name: aggregatorlog_id_seq; Type: SEQUENCE; Schema: planet; Owner: -
--

CREATE SEQUENCE aggregatorlog_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: aggregatorlog_id_seq; Type: SEQUENCE OWNED BY; Schema: planet; Owner: -
--

ALTER SEQUENCE aggregatorlog_id_seq OWNED BY aggregatorlog.id;


--
-- Name: feeds_id_seq; Type: SEQUENCE; Schema: planet; Owner: -
--

CREATE SEQUENCE feeds_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: feeds_id_seq; Type: SEQUENCE OWNED BY; Schema: planet; Owner: -
--

ALTER SEQUENCE feeds_id_seq OWNED BY feeds.id;


--
-- Name: posts_id_seq; Type: SEQUENCE; Schema: planet; Owner: -
--

CREATE SEQUENCE posts_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


--
-- Name: posts_id_seq; Type: SEQUENCE OWNED BY; Schema: planet; Owner: -
--

ALTER SEQUENCE posts_id_seq OWNED BY posts.id;


--
-- Name: id; Type: DEFAULT; Schema: planet; Owner: -
--

ALTER TABLE aggregatorlog ALTER COLUMN id SET DEFAULT nextval('aggregatorlog_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: planet; Owner: -
--

ALTER TABLE feeds ALTER COLUMN id SET DEFAULT nextval('feeds_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: planet; Owner: -
--

ALTER TABLE posts ALTER COLUMN id SET DEFAULT nextval('posts_id_seq'::regclass);


--
-- Name: aggregatorlog_pkey; Type: CONSTRAINT; Schema: planet; Owner: -; Tablespace: 
--

ALTER TABLE ONLY aggregatorlog
    ADD CONSTRAINT aggregatorlog_pkey PRIMARY KEY (id);


--
-- Name: feeds_pkey; Type: CONSTRAINT; Schema: planet; Owner: -; Tablespace: 
--

ALTER TABLE ONLY feeds
    ADD CONSTRAINT feeds_pkey PRIMARY KEY (id);


--
-- Name: posts_pkey; Type: CONSTRAINT; Schema: planet; Owner: -; Tablespace: 
--

ALTER TABLE ONLY posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (id);


--
-- Name: aggregatorlog_feed_idx; Type: INDEX; Schema: planet; Owner: -; Tablespace: 
--

CREATE INDEX aggregatorlog_feed_idx ON aggregatorlog USING btree (feed);


--
-- Name: aggregatorlog_feed_ts_idx; Type: INDEX; Schema: planet; Owner: -; Tablespace: 
--

CREATE INDEX aggregatorlog_feed_ts_idx ON aggregatorlog USING btree (feed, ts);


--
-- Name: feeds_feddurl; Type: INDEX; Schema: planet; Owner: -; Tablespace: 
--

CREATE INDEX feeds_feddurl ON feeds USING btree (feedurl);


--
-- Name: feeds_name; Type: INDEX; Schema: planet; Owner: -; Tablespace: 
--

CREATE INDEX feeds_name ON feeds USING btree (name);


--
-- Name: aggregatorlog_feed_fkey; Type: FK CONSTRAINT; Schema: planet; Owner: -
--

ALTER TABLE ONLY aggregatorlog
    ADD CONSTRAINT aggregatorlog_feed_fkey FOREIGN KEY (feed) REFERENCES feeds(id);


--
-- Name: posts_feed_fkey; Type: FK CONSTRAINT; Schema: planet; Owner: -
--

ALTER TABLE ONLY posts
    ADD CONSTRAINT posts_feed_fkey FOREIGN KEY (feed) REFERENCES feeds(id);


--
-- PostgreSQL database dump complete
--

