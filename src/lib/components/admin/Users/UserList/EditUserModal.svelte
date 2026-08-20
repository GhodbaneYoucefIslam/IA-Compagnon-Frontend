<script lang="ts">
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	import { createEventDispatcher, getContext, onMount } from 'svelte';

	import { updateUserById, type UserUpdateForm } from '$lib/apis/users';
	import { createUserProfileForm, type UserProfileForm } from '$lib/types/user';

	import Modal from '$lib/components/common/Modal.svelte';
	import UserProfileFields from '$lib/components/common/UserProfileFields.svelte';

	const i18n: any = getContext('i18n');
	const dispatch = createEventDispatcher();
	dayjs.extend(localizedFormat);

	export let show = false;
	export let selectedUser;
	export let sessionUser;

	let loading = false;
	let _user: UserUpdateForm & UserProfileForm = {
		profile_image_url: '/user.png',
		name: '',
		email: '',
		password: '',
		...createUserProfileForm()
	};

	const submitHandler = async () => {
		loading = true;
		const res = await updateUserById(localStorage.token, selectedUser.id, _user).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		loading = false;

		if (res) {
			dispatch('save');
			show = false;
		}
	};

	onMount(() => {
		if (selectedUser) {
			_user = {
				profile_image_url: selectedUser.profile_image_url ?? '/user.png',
				name: selectedUser.name ?? '',
				email: selectedUser.email ?? '',
				password: '',
				...createUserProfileForm(selectedUser)
			};
		}
	});
</script>

<Modal size="lg" bind:show>
	<div class="max-h-[90dvh] overflow-y-auto">
		<div class="flex justify-between px-5 py-4 dark:text-gray-300">
			<div class="self-center text-lg font-medium">{$i18n.t('Edit User')}</div>
			<button class="self-center" type="button" on:click={() => (show = false)}>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="size-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>
		<hr class="border-gray-100 dark:border-gray-850" />

		<form
			class="flex flex-col gap-4 p-5 dark:text-gray-200"
			on:submit|preventDefault={submitHandler}
		>
			<div class="flex items-center rounded-md px-2 py-1">
				<img
					src={selectedUser.profile_image_url}
					class="mr-4 size-14 rounded-full object-cover"
					alt="Profil utilisateur"
				/>
				<div>
					<div class="font-semibold">{selectedUser.name}</div>
					<div class="text-xs text-gray-500">
						{$i18n.t('Created at')}
						{dayjs(selectedUser.created_at * 1000).format('LL')}
					</div>
				</div>
			</div>

			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
				<label class="flex flex-col gap-1 text-xs text-gray-500">
					{$i18n.t('Email')}
					<input
						class="rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden disabled:text-gray-500 dark:border-gray-800 dark:bg-gray-850"
						type="email"
						bind:value={_user.email}
						autocomplete="off"
						required
						disabled={selectedUser.id === sessionUser.id}
					/>
				</label>

				<label class="flex flex-col gap-1 text-xs text-gray-500">
					Nom d’affichage
					<input
						class="rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-800 dark:bg-gray-850"
						type="text"
						bind:value={_user.name}
						autocomplete="off"
						required
					/>
				</label>

				<label class="flex flex-col gap-1 text-xs text-gray-500 sm:col-span-2">
					{$i18n.t('New Password')}
					<input
						class="rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-800 dark:bg-gray-850"
						type="password"
						bind:value={_user.password}
						autocomplete="new-password"
					/>
				</label>
			</div>

			<UserProfileFields profile={_user} role={selectedUser.role} />

			<p class="text-xs text-gray-500">
				Les valeurs modifiées ici pourront être remplacées lors de la prochaine synchronisation
				Airtable.
			</p>

			<div class="flex justify-end text-sm font-medium">
				<button
					class="rounded-full bg-black px-4 py-2 text-white transition hover:bg-gray-900 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-black"
					type="submit"
					disabled={loading}
				>
					{loading ? 'Enregistrement…' : $i18n.t('Save')}
				</button>
			</div>
		</form>
	</div>
</Modal>
