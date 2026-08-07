<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext } from 'svelte';
	import { addUser, type AddUserForm } from '$lib/apis/auths';
	import { createUserProfileForm, type UserProfileForm } from '$lib/types/user';

	import { WEBUI_BASE_URL } from '$lib/constants';
	import Modal from '$lib/components/common/Modal.svelte';
	import UserProfileFields from '$lib/components/common/UserProfileFields.svelte';

	const i18n: any = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;

	let loading = false;
	let tab = '';
	let inputFiles: FileList | undefined;

	const createEmptyUser = (): AddUserForm & UserProfileForm => ({
		name: '',
		email: '',
		password: '',
		role: 'user',
		...createUserProfileForm()
	});

	let _user = createEmptyUser();

	$: if (show) {
		_user = createEmptyUser();
	}

	const parseCsvRow = (row: string): string[] => {
		const columns: string[] = [];
		let current = '';
		let quoted = false;

		for (let index = 0; index < row.length; index += 1) {
			const character = row[index];
			if (character === '"') {
				if (quoted && row[index + 1] === '"') {
					current += '"';
					index += 1;
				} else {
					quoted = !quoted;
				}
			} else if (character === ',' && !quoted) {
				columns.push(current.trim());
				current = '';
			} else {
				current += character;
			}
		}

		columns.push(current.trim());
		return columns;
	};

	const userFromCsvColumns = (columns: string[]): AddUserForm & UserProfileForm => ({
		name: columns[0] ?? '',
		email: columns[1] ?? '',
		password: columns[2] ?? '',
		role: (columns[3] ?? '').toLowerCase(),
		last_name: columns[4] ?? '',
		first_name: columns[5] ?? '',
		gender: columns[6] ?? '',
		oreegami_edu_email: columns[7] ?? '',
		campus_region: columns[8] ?? '',
		session: columns[9] ?? '',
		rncp_title: columns[10] ?? '',
		apprenticeship_company: columns[11] ?? '',
		apprenticeship_start_date: columns[12] ?? '',
		apprenticeship_end_date: columns[13] ?? ''
	});

	const submitHandler = async () => {
		loading = true;

		try {
			if (tab === '') {
				const res = await addUser(localStorage.token, _user).catch((error) => {
					toast.error(`${error}`);
					return null;
				});

				if (res) {
					dispatch('save');
					show = false;
				}
				return;
			}

			if (!inputFiles?.length) {
				toast.error($i18n.t('File not found.'));
				return;
			}

			const csv = await inputFiles[0].text();
			const rows = csv
				.replace(/^\uFEFF/, '')
				.split(/\r?\n/)
				.filter((row) => row.trim());
			let userCount = 0;

			for (const [index, row] of rows.slice(1).entries()) {
				const columns = parseCsvRow(row);
				const importedUser = userFromCsvColumns(columns);
				const rowNumber = index + 2;

				if (
					columns.length < 4 ||
					columns.length > 14 ||
					!['admin', 'user', 'pending'].includes(importedUser.role)
				) {
					toast.error(`Ligne ${rowNumber} : format invalide.`);
					continue;
				}

				const res = await addUser(localStorage.token, importedUser).catch((error) => {
					toast.error(`Ligne ${rowNumber} : ${error}`);
					return null;
				});

				if (res) {
					userCount += 1;
				}
			}

			toast.success(`${userCount} utilisateur(s) importé(s).`);
			inputFiles = undefined;
			dispatch('save');
			show = false;
		} finally {
			loading = false;
		}
	};
</script>

<Modal size="lg" bind:show>
	<div class="max-h-[90dvh] overflow-y-auto">
		<div class="flex justify-between px-5 pb-2 pt-4 dark:text-gray-300">
			<div class="self-center text-lg font-medium">{$i18n.t('Add User')}</div>
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

		<form
			class="flex flex-col px-5 pb-5 dark:text-gray-200"
			on:submit|preventDefault={submitHandler}
		>
			<div
				class="mb-3 flex w-fit gap-1 overflow-x-auto rounded-full text-center text-sm font-medium"
			>
				<button
					class="min-w-fit rounded-full p-1.5 {tab === ''
						? ''
						: 'text-gray-400 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'}"
					type="button"
					on:click={() => (tab = '')}>{$i18n.t('Form')}</button
				>

				<button
					class="min-w-fit rounded-full p-1.5 {tab === 'import'
						? ''
						: 'text-gray-400 hover:text-gray-700 dark:text-gray-600 dark:hover:text-white'}"
					type="button"
					on:click={() => (tab = 'import')}>{$i18n.t('CSV Import')}</button
				>
			</div>

			{#if tab === ''}
				<div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
					<label class="flex flex-col gap-1 text-xs text-gray-500">
						{$i18n.t('Role')}
						<select
							class="rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-800 dark:bg-gray-850"
							bind:value={_user.role}
							required
						>
							<option value="pending">{$i18n.t('pending')}</option>
							<option value="user">{$i18n.t('user')}</option>
							<option value="admin">{$i18n.t('admin')}</option>
						</select>
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

					<label class="flex flex-col gap-1 text-xs text-gray-500">
						{$i18n.t('Email')}
						<input
							class="rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-800 dark:bg-gray-850"
							type="email"
							bind:value={_user.email}
							required
						/>
					</label>

					<label class="flex flex-col gap-1 text-xs text-gray-500">
						{$i18n.t('Password')}
						<input
							class="rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-800 dark:bg-gray-850"
							type="password"
							bind:value={_user.password}
							autocomplete="new-password"
							required
						/>
					</label>
				</div>

				<UserProfileFields profile={_user} />
			{:else}
				<div>
					<input
						id="upload-user-csv-input"
						hidden
						bind:files={inputFiles}
						type="file"
						accept=".csv,text/csv"
					/>
					<button
						class="w-full rounded-xl border border-dashed py-4 text-center text-sm font-medium hover:bg-gray-100 dark:border-gray-850 dark:hover:bg-gray-850"
						type="button"
						on:click={() => document.getElementById('upload-user-csv-input')?.click()}
					>
						{inputFiles?.length
							? `${inputFiles.length} document(s) sélectionné(s)`
							: 'Cliquez ici pour sélectionner un fichier CSV.'}
					</button>

					<div class="mt-3 text-xs leading-5 text-gray-500">
						Le fichier accepte les 4 colonnes historiques puis, dans l’ordre, les 10 champs du
						profil Oreegami. Les dates utilisent le format <code>AAAA-MM-JJ</code>.
						<a
							class="ml-1 underline dark:text-gray-200"
							href="{WEBUI_BASE_URL}/static/user-import.csv"
							download>Télécharger le modèle CSV.</a
						>
					</div>
				</div>
			{/if}

			<div class="flex justify-end pt-4 text-sm font-medium">
				<button
					class="flex items-center rounded-full bg-black px-4 py-2 text-white transition hover:bg-gray-900 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-black"
					type="submit"
					disabled={loading}
				>
					{loading ? 'Enregistrement…' : $i18n.t('Save')}
				</button>
			</div>
		</form>
	</div>
</Modal>
