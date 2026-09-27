// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Character/LyraCharacterMovementComponent.h"
#include "SSMovementRules.h"
#include "SSCharacterMovementComponent.generated.h"

/**
 * Tactical movement (ADR-024, LOCOMOTION_AUDIT §4 S1): walk / jog / sprint
 * gaits and stance speeds from FSSMovementRules (Core), with weight: slower
 * acceleration, momentum on stopping, little air control. The player's
 * sprint / walk / aim intent travels in the saved moves' compressed flags, so
 * speeds are predicted on the client and authoritative on the server.
 */
UCLASS()
class SSBRIDGE_API USSCharacterMovementComponent : public ULyraCharacterMovementComponent
{
	GENERATED_BODY()

public:
	USSCharacterMovementComponent(const FObjectInitializer& ObjectInitializer);

	virtual void InitializeComponent() override;
	virtual float GetMaxSpeed() const override;
	virtual void UpdateFromCompressedFlags(uint8 Flags) override;
	virtual FNetworkPredictionData_Client* GetPredictionData_Client() const override;

	void SetWantsSprint(bool bWants) { bWantsSprint = bWants; }
	void SetWantsWalk(bool bWants) { bWantsWalk = bWants; }
	void SetWantsAim(bool bWants) { bWantsAim = bWants; }
	bool WantsSprint() const { return bWantsSprint; }
	bool WantsWalk() const { return bWantsWalk; }
	bool WantsAim() const { return bWantsAim; }

	/** The gait in use now (for animation, first person and the HUD). */
	ESSGait GetGait() const;
	ESSStance GetStance() const;

	UPROPERTY(EditDefaultsOnly, Category = "Tactical Movement")
	FSSMovementTuning Tuning;

private:
	void ApplyTuning();

	bool bWantsSprint = false;
	bool bWantsWalk = false;
	bool bWantsAim = false;
};
