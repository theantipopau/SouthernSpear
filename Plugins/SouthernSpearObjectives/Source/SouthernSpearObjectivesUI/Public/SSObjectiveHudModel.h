// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSObjectiveTypes.h"
#include "SSTeamTypes.h"

/** Colour intent for a HUD element, resolved from the viewer's side. */
enum class ESSObjectiveHudTone : uint8
{
	Neutral,
	Friendly,
	Opposing,
	Contested,
};

/**
 * What the objective HUD shows, built from replicated state only.
 *
 * Pure so it can be tested without a viewport. Team words are resolved from
 * the viewer's team (ADR-017): a viewer with no playable team gets the neutral
 * "Team One"/"Team Two" vantage, never a guessed side.
 */
struct SSOBJUI_API FSSObjectiveHudModel
{
	FText Header;
	FText Objective;

	/** Structured parts of Header/Score/Objective for styled display. */
	FText RoundLabel;      // "Round 3"
	FText PhaseLabel;      // "Starts in", "Capture", "Draw", "Friendly win"
	FText Clock;           // "2:06", empty after the round
	FText ObjectiveName;   // "OBJ B  Farmstead"
	FText ObjectiveStatus; // "Opposing capturing"
	FText FirstSide, SecondSide;
	int32 FirstScore = 0, SecondScore = 0;
	ESSObjectiveHudTone FirstTone = ESSObjectiveHudTone::Neutral;
	ESSObjectiveHudTone SecondTone = ESSObjectiveHudTone::Neutral;

	struct FChip
	{
		FText Letter;
		ESSObjectiveHudTone OwnerTone = ESSObjectiveHudTone::Neutral;
		bool bActive = false;
	};
	/** One chip per objective in sequence; empty unless BuildChips is called. */
	TArray<FChip> Chips;

	/** Fill Chips from every objective's state, in sequence order. */
	void BuildChips(TConstArrayView<FSSObjectiveState> Objectives, int32 ActiveIndex, ESSTeamId ViewerTeam);
	FText Score;
	float Progress = 0.f;
	ESSObjectiveHudTone ProgressTone = ESSObjectiveHudTone::Neutral;
	bool bShowObjective = false;

	/**
	 * @param Round       replicated round state
	 * @param Active      active objective's state, or nullptr when none is active
	 * @param ActiveName  active objective's display name
	 * @param ViewerTeam  the local viewer's authoritative team (None for spectators)
	 */
	static FSSObjectiveHudModel Build(const FSSRoundState& Round, const FSSObjectiveState* Active,
		const FText& ActiveName, ESSTeamId ViewerTeam);

	/** Section Assault (ADR-031): the viewer's role this round, "Attack" or "Defend"; empty without a team. */
	FText Role;
	bool bViewerAttacking = false;
	/** Section Assault, in play: players alive, own side first ("5 v 4"); empty otherwise. */
	FText Alive;

	/**
	 * Section Assault: turn a model built by Build into the match view. Scores
	 * become rounds won and the round label counts rounds in this match. Every
	 * string stays short enough for the panel under the minimap: the phase label
	 * is just the role or the result, the alive count has its own field, and the
	 * post-round header is only the reason ("Defenders eliminated").
	 */
	void ApplySectionAssault(const FSSRoundState& Round, const FSSMatchState& Match, ESSTeamId ViewerTeam);

	/** "Friendly"/"Opposing" from the viewer, or "Team One"/"Team Two" without one. */
	static FText TeamWord(ESSTeamId Team, ESSTeamId ViewerTeam);

	static ESSObjectiveHudTone ToneFor(ESSTeamId Team, ESSTeamId ViewerTeam);
};
