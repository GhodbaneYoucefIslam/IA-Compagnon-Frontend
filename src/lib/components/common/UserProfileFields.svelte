<script lang="ts">
	import type { UserProfileForm } from '$lib/types/user';

	export let profile: UserProfileForm;
	export let title = 'Profil Oreegami';
	export let bordered = true;

	const inputClass =
		'w-full rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden focus:border-gray-400 dark:border-gray-800 dark:bg-gray-850 dark:focus:border-gray-600';
</script>

<fieldset class:border={bordered} class="rounded-xl border-gray-100 p-3 dark:border-gray-850">
	<legend class="px-1 text-sm font-medium text-gray-700 dark:text-gray-200">{title}</legend>

	<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Nom
			<input
				class={inputClass}
				type="text"
				bind:value={profile.last_name}
				autocomplete="family-name"
			/>
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Prénom
			<input
				class={inputClass}
				type="text"
				bind:value={profile.first_name}
				autocomplete="given-name"
			/>
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Genre
			<input class={inputClass} type="text" bind:value={profile.gender} autocomplete="sex" />
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			E-mail Oreegami Education
			<input
				class={inputClass}
				type="email"
				bind:value={profile.oreegami_edu_email}
				autocomplete="email"
			/>
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Région du campus
			<input class={inputClass} type="text" bind:value={profile.campus_region} />
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Session
			<input class={inputClass} type="text" bind:value={profile.session} />
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500 sm:col-span-2">
			Titre RNCP
			<input class={inputClass} type="text" bind:value={profile.rncp_title} />
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500 sm:col-span-2">
			Entreprise d’alternance
			<input class={inputClass} type="text" bind:value={profile.apprenticeship_company} />
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Début de l’alternance
			<input
				class={inputClass}
				type="date"
				bind:value={profile.apprenticeship_start_date}
				max={profile.apprenticeship_end_date || undefined}
			/>
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Fin de l’alternance
			<input
				class={inputClass}
				type="date"
				bind:value={profile.apprenticeship_end_date}
				min={profile.apprenticeship_start_date || undefined}
			/>
		</label>
	</div>
</fieldset>
