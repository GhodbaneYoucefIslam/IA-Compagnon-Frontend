<script lang="ts">
	import type { UserProfileForm } from '$lib/types/user';

	export let profile: UserProfileForm;
	export let title = 'Profil Oreegami';
	export let bordered = true;
	export let role = 'user'; // We add this to receive the role from the parent component

	const inputClass =
		'w-full rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden focus:border-gray-400 dark:border-gray-800 dark:bg-gray-850 dark:focus:border-gray-600';
	
	// A CSS class for the dash to match the input height and padding
	const dashClass = 'px-3 py-2 text-sm text-gray-400';
</script>

<fieldset class:border={bordered} class="rounded-xl border-gray-100 p-3 dark:border-gray-850">
	<legend class="px-1 text-sm font-medium text-gray-700 dark:text-gray-200">{title}</legend>

	<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
		<!-- NAME & GENDER: Always editable for everyone (including admins) -->
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

		<!-- OREEGAMI FIELDS: Replaced with a dash for admins -->
		<label class="flex flex-col gap-1 text-xs text-gray-500">
			E-mail Oreegami Education
			{#if role === 'admin'}
				<span class={dashClass}>—</span>
			{:else}
				<input
					class={inputClass}
					type="email"
					bind:value={profile.oreegami_edu_email}
					autocomplete="email"
				/>
			{/if}
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Région du campus
			{#if role === 'admin'}
				<span class={dashClass}>—</span>
			{:else}
				<input class={inputClass} type="text" bind:value={profile.campus_region} />
			{/if}
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Session
			{#if role === 'admin'}
				<span class={dashClass}>—</span>
			{:else}
				<input class={inputClass} type="text" bind:value={profile.session} />
			{/if}
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500 sm:col-span-2">
			Titre RNCP
			{#if role === 'admin'}
				<span class={dashClass}>—</span>
			{:else}
				<input class={inputClass} type="text" bind:value={profile.rncp_title} />
			{/if}
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500 sm:col-span-2">
			Entreprise d’alternance
			{#if role === 'admin'}
				<span class={dashClass}>—</span>
			{:else}
				<input class={inputClass} type="text" bind:value={profile.apprenticeship_company} />
			{/if}
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Début de l’alternance
			{#if role === 'admin'}
				<span class={dashClass}>—</span>
			{:else}
				<input
					class={inputClass}
					type="date"
					bind:value={profile.apprenticeship_start_date}
					max={profile.apprenticeship_end_date || undefined}
				/>
			{/if}
		</label>

		<label class="flex flex-col gap-1 text-xs text-gray-500">
			Fin de l’alternance
			{#if role === 'admin'}
				<span class={dashClass}>—</span>
			{:else}
				<input
					class={inputClass}
					type="date"
					bind:value={profile.apprenticeship_end_date}
					min={profile.apprenticeship_start_date || undefined}
				/>
			{/if}
		</label>
	</div>
</fieldset>