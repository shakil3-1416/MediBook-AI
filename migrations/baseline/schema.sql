-- MediBook baseline schema at alembic revision m6b2queue20260930.
-- Schema-only pg_dump of a database migrated to that revision.
-- Loaded by app/db_bootstrap.py into EMPTY databases only; existing databases run alembic.
--
-- PostgreSQL database dump
--

-- Dumped from database version 17.10
-- Dumped by pg_dump version 17.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;

--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);

--
-- Name: appointment_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.appointment_events (
    appointment_id uuid NOT NULL,
    event_type character varying(40) NOT NULL,
    payload jsonb NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

--
-- Name: appointments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.appointments (
    doctor_id uuid NOT NULL,
    doctor_slot_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    consultation_fee numeric(10,2) NOT NULL,
    status character varying(30) NOT NULL,
    confirmation_code character varying(32) NOT NULL,
    booked_at timestamp with time zone NOT NULL,
    cancelled_at timestamp with time zone,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    hospital_id uuid NOT NULL
);

--
-- Name: conversation_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_messages (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    actions json,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    title character varying(160) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    archived_at timestamp with time zone
);

--
-- Name: doctor_schedule_exceptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.doctor_schedule_exceptions (
    id uuid NOT NULL,
    hospital_doctor_id uuid NOT NULL,
    exception_date date NOT NULL,
    kind character varying(32) NOT NULL,
    start_time time without time zone,
    end_time time without time zone,
    slot_duration_minutes integer,
    capacity integer,
    reason character varying(500),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_schedule_exception_capacity CHECK (((capacity IS NULL) OR ((capacity >= 1) AND (capacity <= 50)))),
    CONSTRAINT ck_schedule_exception_duration CHECK (((slot_duration_minutes IS NULL) OR ((slot_duration_minutes >= 5) AND (slot_duration_minutes <= 240)))),
    CONSTRAINT ck_schedule_exception_kind CHECK (((kind)::text = ANY ((ARRAY['leave'::character varying, 'closure'::character varying, 'override'::character varying, 'unavailable'::character varying])::text[]))),
    CONSTRAINT ck_schedule_exception_time CHECK ((((start_time IS NULL) AND (end_time IS NULL)) OR ((start_time IS NOT NULL) AND (end_time IS NOT NULL) AND (start_time < end_time))))
);

--
-- Name: doctor_schedule_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.doctor_schedule_rules (
    id uuid NOT NULL,
    hospital_doctor_id uuid NOT NULL,
    weekday smallint NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    slot_duration_minutes integer NOT NULL,
    capacity integer DEFAULT 1 NOT NULL,
    valid_from date,
    valid_until date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_schedule_rule_capacity CHECK (((capacity >= 1) AND (capacity <= 50))),
    CONSTRAINT ck_schedule_rule_dates CHECK (((valid_until IS NULL) OR (valid_from IS NULL) OR (valid_until >= valid_from))),
    CONSTRAINT ck_schedule_rule_duration CHECK (((slot_duration_minutes >= 5) AND (slot_duration_minutes <= 240))),
    CONSTRAINT ck_schedule_rule_time CHECK ((start_time < end_time)),
    CONSTRAINT ck_schedule_rule_weekday CHECK (((weekday >= 0) AND (weekday <= 6)))
);

--
-- Name: doctor_slots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.doctor_slots (
    doctor_id uuid NOT NULL,
    slot_date date NOT NULL,
    start_time time without time zone NOT NULL,
    is_available boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    hospital_doctor_id uuid NOT NULL,
    capacity integer DEFAULT 1 NOT NULL,
    is_enabled boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_doctor_slots_capacity CHECK (((capacity >= 1) AND (capacity <= 50)))
);

--
-- Name: doctors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.doctors (
    full_name character varying(200) NOT NULL,
    gender character varying(30),
    qualification character varying(500),
    experience_years integer NOT NULL,
    specialty_id uuid NOT NULL,
    clinic_name character varying(200) NOT NULL,
    clinic_location character varying(250) NOT NULL,
    consultation_fee numeric(10,2) NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

--
-- Name: email_verification_challenges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_verification_challenges (
    id uuid NOT NULL,
    email character varying(320) NOT NULL,
    full_name character varying(200) NOT NULL,
    phone character varying(32) NOT NULL,
    gender character varying(32) NOT NULL,
    password_hash character varying(500) NOT NULL,
    profile_image_url character varying(1000),
    code_hash character varying(128) NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    resend_available_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: hospital_copilot_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospital_copilot_events (
    id character varying(36) NOT NULL,
    hospital_id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    event_type character varying(64) NOT NULL,
    proposal_id character varying(36),
    detail json NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: hospital_copilot_proposals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospital_copilot_proposals (
    id character varying(36) NOT NULL,
    hospital_id character varying(36) NOT NULL,
    created_by_user_id character varying(36) NOT NULL,
    action_type character varying(64) NOT NULL,
    payload json NOT NULL,
    impact json NOT NULL,
    status character varying(32) DEFAULT 'pending'::character varying NOT NULL,
    execution_supported boolean DEFAULT false NOT NULL,
    execution_result json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    confirmed_at timestamp with time zone,
    executed_at timestamp with time zone,
    cancelled_at timestamp with time zone
);

--
-- Name: hospital_doctors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospital_doctors (
    id uuid NOT NULL,
    hospital_id uuid NOT NULL,
    doctor_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    source_mode character varying(32) DEFAULT 'managed'::character varying NOT NULL,
    external_doctor_id character varying(255),
    clinic_name character varying(200),
    clinic_location character varying(250),
    consultation_fee numeric(10,2),
    public_profile jsonb DEFAULT '{}'::jsonb NOT NULL,
    operational_metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_hospital_doctors_source_mode CHECK (((source_mode)::text = ANY ((ARRAY['managed'::character varying, 'connected'::character varying, 'hybrid'::character varying])::text[])))
);

--
-- Name: hospital_integrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospital_integrations (
    id uuid NOT NULL,
    hospital_id uuid NOT NULL,
    provider character varying(64) NOT NULL,
    status character varying(32) DEFAULT 'not_configured'::character varying NOT NULL,
    config jsonb DEFAULT '{}'::jsonb NOT NULL,
    last_checked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    integration_type character varying(64) DEFAULT 'custom'::character varying NOT NULL,
    source_mode character varying(32) DEFAULT 'managed'::character varying NOT NULL,
    sync_status character varying(32) DEFAULT 'idle'::character varying NOT NULL,
    ownership jsonb DEFAULT '{}'::jsonb NOT NULL,
    last_sync_at timestamp with time zone,
    last_error character varying(500),
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_hospital_integrations_source_mode CHECK (((source_mode)::text = ANY ((ARRAY['managed'::character varying, 'connected'::character varying, 'hybrid'::character varying])::text[]))),
    CONSTRAINT ck_hospital_integrations_sync_status CHECK (((sync_status)::text = ANY ((ARRAY['idle'::character varying, 'running'::character varying, 'succeeded'::character varying, 'failed'::character varying])::text[])))
);

--
-- Name: hospital_memberships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospital_memberships (
    id uuid NOT NULL,
    hospital_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role character varying(32) DEFAULT 'hospital_staff'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: hospital_operations_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospital_operations_audit (
    id uuid NOT NULL,
    hospital_id uuid NOT NULL,
    actor_user_id uuid,
    entity_type character varying(64) NOT NULL,
    entity_id uuid,
    action character varying(64) NOT NULL,
    before_state jsonb DEFAULT '{}'::jsonb NOT NULL,
    after_state jsonb DEFAULT '{}'::jsonb NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: hospital_platform_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospital_platform_settings (
    hospital_id character varying(36) NOT NULL,
    data_mode character varying(32) DEFAULT 'managed'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: hospitals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospitals (
    id uuid NOT NULL,
    slug character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    status character varying(32) DEFAULT 'active'::character varying NOT NULL,
    timezone character varying(64) DEFAULT 'Asia/Dhaka'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: identity_verification_challenges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.identity_verification_challenges (
    id uuid NOT NULL,
    purpose character varying(32) NOT NULL,
    user_id uuid NOT NULL,
    email character varying(320) NOT NULL,
    code_hash character varying(64) NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    resend_available_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    consumed_at timestamp with time zone
);

--
-- Name: integration_sync_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.integration_sync_runs (
    id character varying(36) NOT NULL,
    hospital_id character varying(36) NOT NULL,
    integration_id character varying(36) NOT NULL,
    provider character varying(64) NOT NULL,
    resource character varying(80) NOT NULL,
    direction character varying(16) NOT NULL,
    status character varying(24) NOT NULL,
    idempotency_key character varying(200) NOT NULL,
    attempt integer DEFAULT 1 NOT NULL,
    records_seen integer DEFAULT 0 NOT NULL,
    records_changed integer DEFAULT 0 NOT NULL,
    last_error character varying(1000),
    result json DEFAULT '{}'::json NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    max_attempts integer DEFAULT 3 NOT NULL,
    next_attempt_at timestamp with time zone,
    heartbeat_at timestamp with time zone,
    claimed_by character varying(120),
    last_attempt_at timestamp with time zone
);

--
-- Name: patients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.patients (
    full_name character varying(200) NOT NULL,
    phone character varying(30) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

--
-- Name: platform_control_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform_control_events (
    id character varying(36) NOT NULL,
    hospital_id character varying(36),
    actor_user_id character varying(36) NOT NULL,
    event_type character varying(80) NOT NULL,
    detail json NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: specialties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.specialties (
    name character varying(100) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(320) NOT NULL,
    password_hash character varying(512) NOT NULL,
    full_name character varying(200) NOT NULL,
    phone character varying(20) NOT NULL,
    role character varying(30) DEFAULT 'patient'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    gender character varying(32),
    profile_image_url character varying(1000),
    email_verified_at timestamp with time zone
);

--
-- Name: widget_conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.widget_conversations (
    id uuid NOT NULL,
    hospital_id uuid NOT NULL,
    visitor_id character varying(128) NOT NULL,
    title character varying(255) DEFAULT 'New appointment chat'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: widget_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.widget_messages (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    role character varying(16) NOT NULL,
    content text NOT NULL,
    sequence_no integer NOT NULL,
    edited_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_widget_message_role CHECK (((role)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying])::text[])))
);

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);

--
-- Name: appointment_events appointment_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointment_events
    ADD CONSTRAINT appointment_events_pkey PRIMARY KEY (id);

--
-- Name: appointments appointments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);

--
-- Name: conversation_messages conversation_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_pkey PRIMARY KEY (id);

--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);

--
-- Name: doctor_schedule_exceptions doctor_schedule_exceptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_schedule_exceptions
    ADD CONSTRAINT doctor_schedule_exceptions_pkey PRIMARY KEY (id);

--
-- Name: doctor_schedule_rules doctor_schedule_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_schedule_rules
    ADD CONSTRAINT doctor_schedule_rules_pkey PRIMARY KEY (id);

--
-- Name: doctor_slots doctor_slots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_slots
    ADD CONSTRAINT doctor_slots_pkey PRIMARY KEY (id);

--
-- Name: doctors doctors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_pkey PRIMARY KEY (id);

--
-- Name: email_verification_challenges email_verification_challenges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_verification_challenges
    ADD CONSTRAINT email_verification_challenges_pkey PRIMARY KEY (id);

--
-- Name: hospital_copilot_events hospital_copilot_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_copilot_events
    ADD CONSTRAINT hospital_copilot_events_pkey PRIMARY KEY (id);

--
-- Name: hospital_copilot_proposals hospital_copilot_proposals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_copilot_proposals
    ADD CONSTRAINT hospital_copilot_proposals_pkey PRIMARY KEY (id);

--
-- Name: hospital_doctors hospital_doctors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_doctors
    ADD CONSTRAINT hospital_doctors_pkey PRIMARY KEY (id);

--
-- Name: hospital_integrations hospital_integrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_integrations
    ADD CONSTRAINT hospital_integrations_pkey PRIMARY KEY (id);

--
-- Name: hospital_memberships hospital_memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_memberships
    ADD CONSTRAINT hospital_memberships_pkey PRIMARY KEY (id);

--
-- Name: hospital_operations_audit hospital_operations_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_operations_audit
    ADD CONSTRAINT hospital_operations_audit_pkey PRIMARY KEY (id);

--
-- Name: hospital_platform_settings hospital_platform_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_platform_settings
    ADD CONSTRAINT hospital_platform_settings_pkey PRIMARY KEY (hospital_id);

--
-- Name: hospitals hospitals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospitals
    ADD CONSTRAINT hospitals_pkey PRIMARY KEY (id);

--
-- Name: identity_verification_challenges identity_verification_challenges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.identity_verification_challenges
    ADD CONSTRAINT identity_verification_challenges_pkey PRIMARY KEY (id);

--
-- Name: integration_sync_runs integration_sync_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_sync_runs
    ADD CONSTRAINT integration_sync_runs_pkey PRIMARY KEY (id);

--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);

--
-- Name: platform_control_events platform_control_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_control_events
    ADD CONSTRAINT platform_control_events_pkey PRIMARY KEY (id);

--
-- Name: specialties specialties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.specialties
    ADD CONSTRAINT specialties_pkey PRIMARY KEY (id);

--
-- Name: hospital_doctors uq_hospital_doctor; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_doctors
    ADD CONSTRAINT uq_hospital_doctor UNIQUE (hospital_id, doctor_id);

--
-- Name: hospital_doctors uq_hospital_doctor_external_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_doctors
    ADD CONSTRAINT uq_hospital_doctor_external_id UNIQUE (hospital_id, external_doctor_id);

--
-- Name: doctor_slots uq_hospital_doctor_slot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_slots
    ADD CONSTRAINT uq_hospital_doctor_slot UNIQUE (hospital_doctor_id, slot_date, start_time);

--
-- Name: hospital_integrations uq_hospital_integration; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_integrations
    ADD CONSTRAINT uq_hospital_integration UNIQUE (hospital_id, provider);

--
-- Name: hospital_memberships uq_hospital_membership; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_memberships
    ADD CONSTRAINT uq_hospital_membership UNIQUE (hospital_id, user_id);

--
-- Name: hospitals uq_hospitals_slug; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospitals
    ADD CONSTRAINT uq_hospitals_slug UNIQUE (slug);

--
-- Name: integration_sync_runs uq_integration_sync_runs_idempotency; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.integration_sync_runs
    ADD CONSTRAINT uq_integration_sync_runs_idempotency UNIQUE (integration_id, idempotency_key);

--
-- Name: widget_messages uq_widget_message_sequence; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.widget_messages
    ADD CONSTRAINT uq_widget_message_sequence UNIQUE (conversation_id, sequence_no);

--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

--
-- Name: widget_conversations widget_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.widget_conversations
    ADD CONSTRAINT widget_conversations_pkey PRIMARY KEY (id);

--
-- Name: widget_messages widget_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.widget_messages
    ADD CONSTRAINT widget_messages_pkey PRIMARY KEY (id);

--
-- Name: ix_active_appointment_slot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_active_appointment_slot ON public.appointments USING btree (doctor_slot_id) WHERE ((status)::text = ANY ((ARRAY['confirmed'::character varying, 'checked_in'::character varying])::text[]));

--
-- Name: ix_appointment_events_appointment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointment_events_appointment_id ON public.appointment_events USING btree (appointment_id);

--
-- Name: ix_appointment_events_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointment_events_event_type ON public.appointment_events USING btree (event_type);

--
-- Name: ix_appointments_confirmation_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_appointments_confirmation_code ON public.appointments USING btree (confirmation_code);

--
-- Name: ix_appointments_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointments_doctor_id ON public.appointments USING btree (doctor_id);

--
-- Name: ix_appointments_doctor_slot_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointments_doctor_slot_id ON public.appointments USING btree (doctor_slot_id);

--
-- Name: ix_appointments_hospital_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointments_hospital_id ON public.appointments USING btree (hospital_id);

--
-- Name: ix_appointments_patient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointments_patient_id ON public.appointments USING btree (patient_id);

--
-- Name: ix_appointments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_appointments_status ON public.appointments USING btree (status);

--
-- Name: ix_conversation_messages_conversation_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversation_messages_conversation_created ON public.conversation_messages USING btree (conversation_id, created_at);

--
-- Name: ix_conversation_messages_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversation_messages_conversation_id ON public.conversation_messages USING btree (conversation_id);

--
-- Name: ix_conversation_messages_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversation_messages_created_at ON public.conversation_messages USING btree (created_at);

--
-- Name: ix_conversations_updated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_updated_at ON public.conversations USING btree (updated_at);

--
-- Name: ix_conversations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_user_id ON public.conversations USING btree (user_id);

--
-- Name: ix_conversations_user_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_user_updated ON public.conversations USING btree (user_id, updated_at);

--
-- Name: ix_copilot_events_hospital_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_copilot_events_hospital_created ON public.hospital_copilot_events USING btree (hospital_id, created_at);

--
-- Name: ix_copilot_events_proposal_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_copilot_events_proposal_id ON public.hospital_copilot_events USING btree (proposal_id);

--
-- Name: ix_copilot_proposals_hospital_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_copilot_proposals_hospital_status ON public.hospital_copilot_proposals USING btree (hospital_id, status);

--
-- Name: ix_doctor_schedule_exceptions_exception_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_schedule_exceptions_exception_date ON public.doctor_schedule_exceptions USING btree (exception_date);

--
-- Name: ix_doctor_schedule_exceptions_hospital_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_schedule_exceptions_hospital_doctor_id ON public.doctor_schedule_exceptions USING btree (hospital_doctor_id);

--
-- Name: ix_doctor_schedule_exceptions_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_schedule_exceptions_is_active ON public.doctor_schedule_exceptions USING btree (is_active);

--
-- Name: ix_doctor_schedule_rules_hospital_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_schedule_rules_hospital_doctor_id ON public.doctor_schedule_rules USING btree (hospital_doctor_id);

--
-- Name: ix_doctor_schedule_rules_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_schedule_rules_is_active ON public.doctor_schedule_rules USING btree (is_active);

--
-- Name: ix_doctor_slots_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_slots_doctor_id ON public.doctor_slots USING btree (doctor_id);

--
-- Name: ix_doctor_slots_hospital_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_slots_hospital_doctor_id ON public.doctor_slots USING btree (hospital_doctor_id);

--
-- Name: ix_doctor_slots_is_available; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_slots_is_available ON public.doctor_slots USING btree (is_available);

--
-- Name: ix_doctor_slots_slot_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctor_slots_slot_date ON public.doctor_slots USING btree (slot_date);

--
-- Name: ix_doctors_clinic_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctors_clinic_location ON public.doctors USING btree (clinic_location);

--
-- Name: ix_doctors_full_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctors_full_name ON public.doctors USING btree (full_name);

--
-- Name: ix_doctors_gender; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctors_gender ON public.doctors USING btree (gender);

--
-- Name: ix_doctors_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctors_is_active ON public.doctors USING btree (is_active);

--
-- Name: ix_doctors_specialty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_doctors_specialty_id ON public.doctors USING btree (specialty_id);

--
-- Name: ix_email_verification_challenges_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_verification_challenges_email ON public.email_verification_challenges USING btree (email);

--
-- Name: ix_hospital_doctors_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_doctors_doctor_id ON public.hospital_doctors USING btree (doctor_id);

--
-- Name: ix_hospital_doctors_external_doctor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_doctors_external_doctor_id ON public.hospital_doctors USING btree (external_doctor_id);

--
-- Name: ix_hospital_doctors_hospital_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_doctors_hospital_id ON public.hospital_doctors USING btree (hospital_id);

--
-- Name: ix_hospital_doctors_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_doctors_is_active ON public.hospital_doctors USING btree (is_active);

--
-- Name: ix_hospital_doctors_source_mode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_doctors_source_mode ON public.hospital_doctors USING btree (source_mode);

--
-- Name: ix_hospital_integrations_hospital_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_integrations_hospital_status ON public.hospital_integrations USING btree (hospital_id, status);

--
-- Name: ix_hospital_operations_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_operations_audit_action ON public.hospital_operations_audit USING btree (action);

--
-- Name: ix_hospital_operations_audit_actor_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_operations_audit_actor_user_id ON public.hospital_operations_audit USING btree (actor_user_id);

--
-- Name: ix_hospital_operations_audit_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_operations_audit_entity_id ON public.hospital_operations_audit USING btree (entity_id);

--
-- Name: ix_hospital_operations_audit_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_operations_audit_entity_type ON public.hospital_operations_audit USING btree (entity_type);

--
-- Name: ix_hospital_operations_audit_hospital_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_operations_audit_hospital_id ON public.hospital_operations_audit USING btree (hospital_id);

--
-- Name: ix_hospital_ops_audit_hospital_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hospital_ops_audit_hospital_created ON public.hospital_operations_audit USING btree (hospital_id, created_at);

--
-- Name: ix_identity_verification_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_identity_verification_email ON public.identity_verification_challenges USING btree (email);

--
-- Name: ix_identity_verification_user_purpose; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_identity_verification_user_purpose ON public.identity_verification_challenges USING btree (user_id, purpose);

--
-- Name: ix_integration_sync_runs_hospital_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_integration_sync_runs_hospital_created ON public.integration_sync_runs USING btree (hospital_id, created_at);

--
-- Name: ix_integration_sync_runs_integration_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_integration_sync_runs_integration_created ON public.integration_sync_runs USING btree (integration_id, created_at);

--
-- Name: ix_integration_sync_runs_queue; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_integration_sync_runs_queue ON public.integration_sync_runs USING btree (status, next_attempt_at, created_at);

--
-- Name: ix_patients_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_patients_phone ON public.patients USING btree (phone);

--
-- Name: ix_platform_control_events_actor_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_platform_control_events_actor_created ON public.platform_control_events USING btree (actor_user_id, created_at);

--
-- Name: ix_platform_control_events_hospital_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_platform_control_events_hospital_created ON public.platform_control_events USING btree (hospital_id, created_at);

--
-- Name: ix_schedule_exception_hospital_doctor_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_schedule_exception_hospital_doctor_date ON public.doctor_schedule_exceptions USING btree (hospital_doctor_id, exception_date);

--
-- Name: ix_schedule_rule_hospital_doctor_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_schedule_rule_hospital_doctor_active ON public.doctor_schedule_rules USING btree (hospital_doctor_id, is_active);

--
-- Name: ix_specialties_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_specialties_name ON public.specialties USING btree (name);

--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);

--
-- Name: ix_users_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_phone ON public.users USING btree (phone);

--
-- Name: ix_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_role ON public.users USING btree (role);

--
-- Name: ix_widget_conversations_hospital_visitor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_widget_conversations_hospital_visitor ON public.widget_conversations USING btree (hospital_id, visitor_id, updated_at DESC);

--
-- Name: ix_widget_messages_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_widget_messages_conversation ON public.widget_messages USING btree (conversation_id, sequence_no);

--
-- Name: uq_hospitals_slug_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_hospitals_slug_idx ON public.hospitals USING btree (slug);

--
-- Name: appointment_events appointment_events_appointment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointment_events
    ADD CONSTRAINT appointment_events_appointment_id_fkey FOREIGN KEY (appointment_id) REFERENCES public.appointments(id) ON DELETE CASCADE;

--
-- Name: appointments appointments_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE RESTRICT;

--
-- Name: appointments appointments_doctor_slot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_doctor_slot_id_fkey FOREIGN KEY (doctor_slot_id) REFERENCES public.doctor_slots(id) ON DELETE RESTRICT;

--
-- Name: appointments appointments_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id) ON DELETE RESTRICT;

--
-- Name: conversation_messages conversation_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;

--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

--
-- Name: doctor_schedule_exceptions doctor_schedule_exceptions_hospital_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_schedule_exceptions
    ADD CONSTRAINT doctor_schedule_exceptions_hospital_doctor_id_fkey FOREIGN KEY (hospital_doctor_id) REFERENCES public.hospital_doctors(id) ON DELETE CASCADE;

--
-- Name: doctor_schedule_rules doctor_schedule_rules_hospital_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_schedule_rules
    ADD CONSTRAINT doctor_schedule_rules_hospital_doctor_id_fkey FOREIGN KEY (hospital_doctor_id) REFERENCES public.hospital_doctors(id) ON DELETE CASCADE;

--
-- Name: doctor_slots doctor_slots_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_slots
    ADD CONSTRAINT doctor_slots_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;

--
-- Name: doctors doctors_specialty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_specialty_id_fkey FOREIGN KEY (specialty_id) REFERENCES public.specialties(id) ON DELETE RESTRICT;

--
-- Name: appointments fk_appointments_hospital_id_hospitals; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT fk_appointments_hospital_id_hospitals FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE RESTRICT;

--
-- Name: doctor_slots fk_doctor_slots_hospital_doctor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.doctor_slots
    ADD CONSTRAINT fk_doctor_slots_hospital_doctor FOREIGN KEY (hospital_doctor_id) REFERENCES public.hospital_doctors(id) ON DELETE CASCADE;

--
-- Name: hospital_doctors hospital_doctors_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_doctors
    ADD CONSTRAINT hospital_doctors_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;

--
-- Name: hospital_doctors hospital_doctors_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_doctors
    ADD CONSTRAINT hospital_doctors_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE CASCADE;

--
-- Name: hospital_integrations hospital_integrations_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_integrations
    ADD CONSTRAINT hospital_integrations_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE CASCADE;

--
-- Name: hospital_memberships hospital_memberships_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_memberships
    ADD CONSTRAINT hospital_memberships_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE CASCADE;

--
-- Name: hospital_memberships hospital_memberships_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_memberships
    ADD CONSTRAINT hospital_memberships_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

--
-- Name: hospital_operations_audit hospital_operations_audit_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_operations_audit
    ADD CONSTRAINT hospital_operations_audit_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.users(id) ON DELETE SET NULL;

--
-- Name: hospital_operations_audit hospital_operations_audit_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospital_operations_audit
    ADD CONSTRAINT hospital_operations_audit_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE CASCADE;

--
-- Name: identity_verification_challenges identity_verification_challenges_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.identity_verification_challenges
    ADD CONSTRAINT identity_verification_challenges_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

--
-- Name: widget_conversations widget_conversations_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.widget_conversations
    ADD CONSTRAINT widget_conversations_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(id) ON DELETE CASCADE;

--
-- Name: widget_messages widget_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.widget_messages
    ADD CONSTRAINT widget_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.widget_conversations(id) ON DELETE CASCADE;

--
-- PostgreSQL database dump complete
--
