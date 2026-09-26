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

	/** "Friendly"/"Opposing" from the viewer, or "Team One"/"Team Two" without one. */
	static FText TeamWord(ESSTeamId Team, ESSTeamId ViewerTeam);

	static ESSObjectiveHudTone ToneFor(ESSTeamId Team, ESSTeamId ViewerTeam);
};
