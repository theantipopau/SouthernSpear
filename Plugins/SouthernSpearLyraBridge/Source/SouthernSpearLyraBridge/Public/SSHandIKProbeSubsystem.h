// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSHandIKProbeSubsystem.generated.h"

class USSHandIKMeshComponent;

/**
 * TEMPORARY dev probe (Session 070) — not for commit.
 *
 * `-SSHandIKProbe` on a game run logs, every 0.5 s for 5 s once the first-person view model exists:
 *  - where the left-hand IK leaves the hand, the weapon's grip socket, and the distance between them
 *  - the shoulder-to-target reach against the component's own MaxReachFactor gate and the arm length
 *  - each hand's own frame read off its finger bones (thumb, fingers, palm normal), the weapon-frame pose
 *    that frame should hold (palm across the handguard, thumb down the bore), and the three axis errors
 *  - the hand rotation that would carry the measured frame onto that target, as a ready config offset
 * and, once, every visible mesh component of the pawn (and anything attached to it) with its mesh and
 * material 0, to identify untextured parts.
 *
 * `-SSHandIKProbeNoRotate` (with it) turns the arms' hand rotation off for the run, so the hand is measured
 * as its own clip leaves it: that is the pose an offset has to be solved from, and the only one where the
 * hand rel-to-weapon figure means "what the animation holds" rather than "what the last offset did".
 *
 * Read-only apart from that one flag; it changes no pose and no other property.
 */
UCLASS()
class SSBRIDGE_API USSHandIKProbeSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	/** Ablation (ss.Probe.Hide): hide mesh components whose name or mesh matches, to identify one. */
	void HideMatching(AActor& Pawn);
	/** Every mesh component on the pawn and on actors attached to it (the weapon rides the body mesh). */
	void ListMeshes(AActor& Pawn, const TArray<USSHandIKMeshComponent*>& Arms);
	void Sample(const TArray<USSHandIKMeshComponent*>& Arms, float Elapsed);

	TWeakObjectPtr<AActor> ProbePawn;
	bool bEnabled = false;
	/** -SSHandIKProbeNoRotate: keep the arms' hand as the clip leaves it (bRotateHandToGrip forced off). */
	bool bNoRotate = false;
	bool bStarted = false;
	bool bListed = false;
	bool bDone = false;
	float Elapsed = 0.f;
	float NextSample = 0.f;
	int32 Samples = 0;
};
