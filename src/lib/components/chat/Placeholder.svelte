<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { marked } from 'marked';

	import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
	import { blur, fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	import { config, user, models as _models, temporaryChatEnabled } from '$lib/stores';
	import { sanitizeResponseContent, extractCurlyBraceWords } from '$lib/utils';
	import { WEBUI_BASE_URL } from '$lib/constants';

	import Suggestions from './Suggestions.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
	import MessageInput from './MessageInput.svelte';

	const i18n = getContext('i18n');

	export let transparentBackground = false;

	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;

	export let atSelectedModel: Model | undefined;
	export let selectedModels: [''];

	export let history;

	export let prompt = '';
	export let files = [];

	export let selectedToolIds = [];
	export let imageGenerationEnabled = false;
	export let codeInterpreterEnabled = false;
	export let webSearchEnabled = false;

	export let toolServers = [];

	let models = [];

	let oreegamiSuggestions = [
		// --- LOGISTIQUE, ABSENCES & RETARDS ---
		{
			title: ["Absence ou retard", "La marche à suivre"],
			content: "Je vais avoir du retard (ou une absence) aujourd'hui. Quelles sont les étapes obligatoires à respecter pour prévenir l'école et que se passe-t-il si je n'ai pas de justificatif ?"
		},
		{
			title: ["Problème dans le campus", "Qui contacter"],
			content: "Qui dois-je contacter en cas de problème pédagiques sur mon campus ?"
		},

		// --- RECHERCHE D'ALTERNANCE ---
		{
			title: ["Trouver mon alternance", "Deadlines et démarches"],
			content: "Quelles sont les deadlines maximales pour signer mon contrat d'alternance (apprentissage ou professionnalisation) après le Bootcamp, et que dois-je faire dès que j'ai trouvé une entreprise ?"
		},

		// --- PARCOURS PRO & POSTURE EN ENTREPRISE ---
		{
			title: ["Codes de l'entreprise", "Communication et posture"],
			content: "Je vis une situation stressante ou nouvelle avec mon manager en entreprise et je ne sais pas comment réagir ou formuler ma demande en respectant les codes pros. Peux-tu m'aider ?"
		},
		{
			title: ["Gestion des deadlines", "Stress professionnel"],
			content: "Je me sens submergé par les deadlines et les responsabilités dans ma boîte d'accueil. Comment puis-je communiquer sainement sur ma charge de travail avec mon tuteur ?"
		},

		// --- ACADÉMIQUE & ENTRAÎNEMENT ---
		{
			title: ["Gestion du temps", "E-learning vs Entreprise"],
			content: "J'ai du mal à concilier mes tâches au travail et mes 5 heures d'e-learning hebdomadaires obligatoires sur Teach Up. Peux-tu m'aider à organiser mon planning ?"
		},
		{
			title: ["Outils Oreegami", "Slack, Classroom, Teach Up"],
			content: "Peux-tu me faire un récapitulatif des différents outils utilisés pendant ma formation (Edusign, Classroom, Teach Up, Slack) et de leurs usages principaux ?"
		},
		{
			title: ["Outils IA et automatisation", "Comment choisir"],
			content: "Peux-tu me faire un récapitulatif des différents outils IA utilisés dans l'automatisation des taches répétitives et comment choisir le meilleur outil selon le problème"
		},

		// --- ÉVALUATIONS & EXAMENS ---
		{
			title: ["Système d'évaluation", "QCM, Hackathons..."],
			content: "Comment fonctionne le système d'évaluation chez Oreegami pour valider mon titre RNCP Niveau 6 ?"
		},
		{
			title: ["Le Grand Oral", "Préparer la soutenance"],
			content: "Comment se déroule la soutenance finale (Grand Oral) de 30 minutes, et sur quoi repose l'échange avec le jury ?"
		},

		// --- CARRIÈRE & LONG TERME ---
		{
			title: ["Veille technologique", "Se tenir à jour"],
			content: "En tant qu'Oreegamer, comment puis-je mettre en place une routine efficace de veille technologique pour mon métier (Marketing Digital ou No-Code/IA) ?"
		}
	];

	const selectSuggestionPrompt = async (p) => {
		let text = p;

		if (p.includes('{{CLIPBOARD}}')) {
			const clipboardText = await navigator.clipboard.readText().catch((err) => {
				toast.error($i18n.t('Failed to read clipboard contents'));
				return '{{CLIPBOARD}}';
			});

			text = p.replaceAll('{{CLIPBOARD}}', clipboardText);

			console.log('Clipboard text:', clipboardText, text);
		}

		prompt = text;

		console.log(prompt);
		await tick();

		const chatInputContainerElement = document.getElementById('chat-input-container');
		const chatInputElement = document.getElementById('chat-input');

		if (chatInputContainerElement) {
			chatInputContainerElement.scrollTop = chatInputContainerElement.scrollHeight;
		}

		await tick();
		if (chatInputElement) {
			chatInputElement.focus();
			chatInputElement.dispatchEvent(new Event('input'));
		}

		await tick();
	};

	let selectedModelIdx = 0;

	$: if (selectedModels.length > 0) {
		selectedModelIdx = models.length - 1;
	}

	$: models = selectedModels.map((id) => $_models.find((m) => m.id === id));

	onMount(() => {});
</script>

<div class="m-auto w-full max-w-6xl px-2 @2xl:px-20 translate-y-6 py-24 text-center">
	{#if $temporaryChatEnabled}
		<Tooltip
			content={$i18n.t('This chat won’t appear in history and your messages will not be saved.')}
			className="w-full flex justify-center mb-0.5"
			placement="top"
		>
			<div class="flex items-center gap-2 text-gray-500 font-medium text-lg my-2 w-fit">
				<EyeSlash strokeWidth="2.5" className="size-5" />{$i18n.t('Temporary Chat')}
			</div>
		</Tooltip>
	{/if}

	<div
		class="w-full text-3xl text-gray-800 dark:text-gray-100 text-center flex items-center gap-4 font-primary"
	>
		<div class="w-full flex flex-col justify-center items-center">
			<div class="flex flex-row justify-center gap-3 @sm:gap-3.5 w-fit px-5">
				<div class="flex shrink-0 justify-center">
					<div class="flex -space-x-4 mb-0.5" in:fade={{ duration: 100 }}>
						{#each models as model, modelIdx}
							<Tooltip
								content={(models[modelIdx]?.info?.meta?.tags ?? [])
									.map((tag) => tag.name.toUpperCase())
									.join(', ')}
								placement="top"
							>
								<button
									on:click={() => {
										selectedModelIdx = modelIdx;
									}}
								>
									<img
										crossorigin="anonymous"
										src={model?.info?.meta?.profile_image_url ??
											($i18n.language === 'dg-DG'
												? `/doge.png`
												: `${WEBUI_BASE_URL}/static/favicon.png`)}
										class=" size-9 @sm:size-10 rounded-full border-[1px] border-gray-100 dark:border-none"
										alt="logo"
										draggable="false"
									/>
								</button>
							</Tooltip>
						{/each}
					</div>
				</div>

				<div class=" text-3xl @sm:text-4xl line-clamp-1" in:fade={{ duration: 100 }}>
						{$i18n.t('Hello, {{name}}', { name: $user?.name ??  'Oreegamer'})}
				</div>
			</div>

			<div class="flex mt-1 mb-2">
				<div in:fade={{ duration: 100, delay: 50 }}>
					{#if models[selectedModelIdx]?.info?.meta?.description ?? null}
						<Tooltip
							className=" w-fit"
							content={marked.parse(
								sanitizeResponseContent(models[selectedModelIdx]?.info?.meta?.description ?? '')
							)}
							placement="top"
						>
							<div
								class="mt-0.5 px-2 text-sm font-normal text-gray-500 dark:text-gray-400 line-clamp-2 max-w-xl markdown"
							>
								{@html marked.parse(
									sanitizeResponseContent(models[selectedModelIdx]?.info?.meta?.description)
								)}
							</div>
						</Tooltip>

						{#if models[selectedModelIdx]?.info?.meta?.user}
							<div class="mt-0.5 text-sm font-normal text-gray-400 dark:text-gray-500">
								By
								{#if models[selectedModelIdx]?.info?.meta?.user.community}
									<a
										href="https://openwebui.com/m/{models[selectedModelIdx]?.info?.meta?.user
											.username}"
										>{models[selectedModelIdx]?.info?.meta?.user.name
											? models[selectedModelIdx]?.info?.meta?.user.name
											: `@${models[selectedModelIdx]?.info?.meta?.user.username}`}</a
									>
								{:else}
									{models[selectedModelIdx]?.info?.meta?.user.name}
								{/if}
							</div>
						{/if}
					{/if}
				</div>
			</div>

			<div class="text-base font-normal @md:max-w-3xl w-full py-3 {atSelectedModel ? 'mt-2' : ''}">
				<MessageInput
					{history}
					{selectedModels}
					bind:files
					bind:prompt
					bind:autoScroll
					bind:selectedToolIds
					bind:imageGenerationEnabled
					bind:codeInterpreterEnabled
					bind:webSearchEnabled
					bind:atSelectedModel
					{toolServers}
					{transparentBackground}
					{stopResponse}
					{createMessagePair}
					placeholder={$i18n.t('How can I help you today?')}
					on:upload={(e) => {
						dispatch('upload', e.detail);
					}}
					on:submit={(e) => {
						dispatch('submit', e.detail);
					}}
				/>
			</div>
		</div>
	</div>
	<div class="mx-auto max-w-2xl font-primary" in:fade={{ duration: 200, delay: 200 }}>
		<div class="mx-5">
			<Suggestions
				suggestionPrompts={oreegamiSuggestions}
				inputValue={prompt}
				on:select={(e) => {
					selectSuggestionPrompt(e.detail);
				}}
			/>
		</div>
	</div>
</div>
