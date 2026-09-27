// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Character/LyraCharacter.h"
#include "SSCharacter.generated.h"

class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

/**
 * The Southern Spear soldier (ADR-024): Lyra's character with the tactical
 * movement component (USSCharacterMovementComponent), and the tactical
 * inputs Lyra does not have: walk (hold Alt), sprint (hold Shift, replacing
 * Lyra's dash), lean (hold Q / E) and aim intent (right mouse, shared with
 * Lyra's ADS). Grenade and melee move to G and V. The inputs live in
 * IMC_SS_Tactical (/SSExp_ObjectiveAssault/Input), above Lyra's contexts.
 * Lean is server-authoritative and replicated (it moves the eyes and hitbox).
 */
UCLASS()
class SSBRIDGE_API ASSCharacter : public ALyraCharacter
{
	GENERATED_BODY()

public:
	ASSCharacter(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/**
	 * The visible soldier (3 ACR / MAF parts, viewer-relative): a child actor on the body mesh,
	 * spawned on every machine (presentation only). Lyra's replicated cosmetic-part chain did not
	 * spawn parts on this pawn (Session 031), so the character owns its soldier directly.
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Tactical")
	FSoftClassPath SoldierPartsClass = FSoftClassPath(TEXT("/SSExp_ObjectiveAssault/Characters/B_SS_Soldier.B_SS_Soldier_C"));

	/** -1 left, 0 none, +1 right. */
	UFUNCTION(BlueprintPure, Category = "Tactical")
	int32 GetLean() const { return Lean; }

private:
	void OnSprint(const FInputActionValue& Value);
	void OnWalk(const FInputActionValue& Value);
	void OnAim(const FInputActionValue& Value);
	void OnLeanLeft(const FInputActionValue& Value);
	void OnLeanRight(const FInputActionValue& Value);
	void UpdateLean();
	void EnsureInputContext();

	UFUNCTION(Server, Reliable)
	void ServerSetLean(int8 NewLean);

	UPROPERTY(Replicated)
	int8 Lean = 0;

	UPROPERTY(Transient)
	TObjectPtr<class UChildActorComponent> Soldier;

	bool bLeanLeftHeld = false;
	bool bLeanRightHeld = false;
	FTimerHandle InputContextTimer;
};
