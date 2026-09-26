// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSViewerTeamTintSubsystem.generated.h"

/**
 * Client-side, viewer-relative team tint (ADR-017, ADR-019).
 *
 * Lyra tints characters by absolute team (one team is always red). This
 * re-tints every pawn from the local viewer's side: own team in the
 * Southern Spear friendly colour, the other team in the opposing colour.
 * Cosmetic only; nothing replicates. A viewer without a playable team keeps
 * Lyra's absolute colours, which imply no side.
 */
UCLASS()
class SSBRIDGE_API USSViewerTeamTintSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Pawns re-tinted on the last pass (diagnostics). */
	int32 GetLastTintedCount() const { return LastTintedCount; }

private:
	float Accumulator = 0.f;
	int32 LastTintedCount = 0;
	int32 LastLoggedCount = INDEX_NONE;
};
