export type UserProfileFields = {
	last_name?: string | null;
	first_name?: string | null;
	gender?: string | null;
	oreegami_edu_email?: string | null;
	campus_region?: string | null;
	session?: string | null;
	rncp_title?: string | null;
	apprenticeship_company?: string | null;
	apprenticeship_start_date?: string | null;
	apprenticeship_end_date?: string | null;
};

export type UserProfileForm = {
	[K in keyof Required<UserProfileFields>]: string;
};

export const USER_PROFILE_KEYS: (keyof UserProfileFields)[] = [
	'last_name',
	'first_name',
	'gender',
	'oreegami_edu_email',
	'campus_region',
	'session',
	'rncp_title',
	'apprenticeship_company',
	'apprenticeship_start_date',
	'apprenticeship_end_date'
];

export const createUserProfileForm = (profile: UserProfileFields = {}): UserProfileForm => ({
	last_name: profile.last_name ?? '',
	first_name: profile.first_name ?? '',
	gender: profile.gender ?? '',
	oreegami_edu_email: profile.oreegami_edu_email ?? '',
	campus_region: profile.campus_region ?? '',
	session: profile.session ?? '',
	rncp_title: profile.rncp_title ?? '',
	apprenticeship_company: profile.apprenticeship_company ?? '',
	apprenticeship_start_date: profile.apprenticeship_start_date ?? '',
	apprenticeship_end_date: profile.apprenticeship_end_date ?? ''
});

export const createUserProfilePayload = (
	profile: UserProfileFields
): Required<UserProfileFields> => {
	const normalize = (value?: string | null) => value?.trim() || null;
	const oreegamiEmail = normalize(profile.oreegami_edu_email);

	return {
		last_name: normalize(profile.last_name),
		first_name: normalize(profile.first_name),
		gender: normalize(profile.gender),
		oreegami_edu_email: oreegamiEmail?.toLowerCase() ?? null,
		campus_region: normalize(profile.campus_region),
		session: normalize(profile.session),
		rncp_title: normalize(profile.rncp_title),
		apprenticeship_company: normalize(profile.apprenticeship_company),
		apprenticeship_start_date: normalize(profile.apprenticeship_start_date),
		apprenticeship_end_date: normalize(profile.apprenticeship_end_date)
	};
};
