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

	/** Blood (presentation, every client): Lyra's damage effects fire GameplayCue.Character.DamageTaken
	 * on the victim; a burst from the VFX pack is spawned at the hit point along the shot. */
	virtual void HandleGameplayCue(UObject* Self, FGameplayTag GameplayCueTag, EGameplayCueEvent::Type EventType, const FGameplayCueParameters& Parameters) override;

	UPROPERTY(EditDefaultsOnly, Category = "Tactical")
	FSoftObjectPath BloodEffect = FSoftObjectPath(TEXT("/Game/Realistic_Starter_VFX_Pack_Vol2/Particles/Blood/P_Blood_Splat_Cone.P_Blood_Splat_Cone"));

	/**
	 * Rifle fire audio (presentation, every client): on GameplayCue.Weapon.Rifle.Fire the AUG recordings
	 * (ADFRC, L-0021) play at the weapon (a random close shot, a distant layer heard across the map, an
	 * outdoor tail; the shooter hears the close shot unspatialised), and Lyra's rifle MetaSound on its
	 * hidden weapon actor is muted. Pistol and shotgun cues keep Lyra's sounds.
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Audio")
	TArray<FSoftObjectPath> RifleCloseShots = {
		FSoftObjectPath(TEXT("/Game/AUG/Sound/AUG/Wavs/AUG_closeShot_01.AUG_closeShot_01")),
		FSoftObjectPath(TEXT("/Game/AUG/Sound/AUG/Wavs/AUG_closeShot_02.AUG_closeShot_02")),
		FSoftObjectPath(TEXT("/Game/AUG/Sound/AUG/Wavs/AUG_closeShot_03.AUG_closeShot_03")) };
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Audio")
	TArray<FSoftObjectPath> RifleDistantShots = {
		FSoftObjectPath(TEXT("/Game/AUG/Sound/AUG/Wavs/AUG_distShot_01.AUG_distShot_01")),
		FSoftObjectPath(TEXT("/Game/AUG/Sound/AUG/Wavs/AUG_distShot_02.AUG_distShot_02")),
		FSoftObjectPath(TEXT("/Game/AUG/Sound/AUG/Wavs/AUG_distShot_03.AUG_distShot_03")) };
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Audio")
	FSoftObjectPath RifleTail = FSoftObjectPath(TEXT("/Game/AUG/Sound/AUG/Wavs/AUG_tailMeadows.AUG_tailMeadows"));

	/**
	 * The visible soldier (3 ACR / MAF parts, viewer-relative): a child actor on the body mesh,
	 * spawned on every machine (presentation only). Lyra's replicated cosmetic-part chain did not
	 * spawn parts on this pawn (Session 031), so the character owns its soldier directly.
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Tactical")
	FSoftClassPath SoldierPartsClass = FSoftClassPath(TEXT("/SSExp_ObjectiveAssault/Characters/B_SS_Soldier.B_SS_Soldier_C"));

	/**
	 * Hit zones (damage model, Session 032): physical materials tagged SS.Zone.Head / Torso / Limb
	 * (Tools/Unreal/setup_damage_model.py), set on every physics body of the soldier by bone name at
	 * BeginPlay, on server and clients, so the server's hit traces report the zone.
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Tactical")
	FSoftObjectPath HeadZone = FSoftObjectPath(TEXT("/SSExp_ObjectiveAssault/Characters/Physics/PM_SS_Head.PM_SS_Head"));
	UPROPERTY(EditDefaultsOnly, Category = "Tactical")
	FSoftObjectPath TorsoZone = FSoftObjectPath(TEXT("/SSExp_ObjectiveAssault/Characters/Physics/PM_SS_Torso.PM_SS_Torso"));
	UPROPERTY(EditDefaultsOnly, Category = "Tactical")
	FSoftObjectPath LimbZone = FSoftObjectPath(TEXT("/SSExp_ObjectiveAssault/Characters/Physics/PM_SS_Limb.PM_SS_Limb"));

	/** Number of physics bodies given each zone (tests and diagnostics). */
	int32 ZoneCounts[3] = { 0, 0, 0 };

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

	/** The zone materials set on the physics bodies: held here, or the garbage collector frees
	 * them and the bodies keep dangling pointers (crash on ragdoll at the first death). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<class UPhysicalMaterial>> ZoneMaterials;

	UPROPERTY(Transient)
	TObjectPtr<class UParticleSystem> BloodSystem;

	void PlayRifleFire();

	UPROPERTY(Transient)
	TArray<TObjectPtr<class USoundBase>> LoadedCloseShots;
	UPROPERTY(Transient)
	TArray<TObjectPtr<class USoundBase>> LoadedDistantShots;
	UPROPERTY(Transient)
	TObjectPtr<class USoundBase> LoadedTail;

	bool bLeanLeftHeld = false;
	bool bLeanRightHeld = false;
	FTimerHandle InputContextTimer;
};
