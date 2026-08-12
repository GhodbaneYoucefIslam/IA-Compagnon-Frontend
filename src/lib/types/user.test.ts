import { describe, expect, it } from 'vitest';

import { createUserProfileForm, createUserProfilePayload } from './user';

describe('user profile helpers', () => {
	it('creates form-safe empty strings from nullable API values', () => {
		expect(
			createUserProfileForm({
				last_name: 'Dupont',
				first_name: null
			})
		).toMatchObject({
			last_name: 'Dupont',
			first_name: '',
			oreegami_edu_email: '',
			apprenticeship_start_date: ''
		});
	});

	it('trims text, lowercases the Oreegami email and sends empty values as null', () => {
		expect(
			createUserProfilePayload({
				last_name: '  Dupont ',
				first_name: '   ',
				oreegami_edu_email: ' JEAN.DUPONT@OREEGAMI-EDU.COM ',
				apprenticeship_start_date: '2026-09-01',
				apprenticeship_end_date: ''
			})
		).toEqual({
			last_name: 'Dupont',
			first_name: null,
			gender: null,
			oreegami_edu_email: 'jean.dupont@oreegami-edu.com',
			campus_region: null,
			session: null,
			rncp_title: null,
			apprenticeship_company: null,
			apprenticeship_start_date: '2026-09-01',
			apprenticeship_end_date: null
		});
	});
});
