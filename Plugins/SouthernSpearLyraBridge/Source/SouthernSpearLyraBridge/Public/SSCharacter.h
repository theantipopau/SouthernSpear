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
	 * The other side's rifles (producer: "the OPFOR should have AK, RPK etc sounds"). Viewer-relative like the
	 * uniforms: to each listener the opposing team is MAF, so its shots are the AK-47 pack's (close layer; the
	 * distant layer and tail are shared). Support weapons (A89 / the MAF counterpart) use the same round as their
	 * rifle, so they take their side's close shots pitched down (SupportPitch).
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Audio")
	TArray<FSoftObjectPath> OpforCloseShots = {
		FSoftObjectPath(TEXT("/Game/AK-47/Sound/AK-47/Wavs/AK-47_Fire_1.AK-47_Fire_1")),
		FSoftObjectPath(TEXT("/Game/AK-47/Sound/AK-47/Wavs/AK-47_Fire_2.AK-47_Fire_2")),
		FSoftObjectPath(TEXT("/Game/AK-47/Sound/AK-47/Wavs/AK-47_Fire_3.AK-47_Fire_3")),
		FSoftObjectPath(TEXT("/Game/AK-47/Sound/AK-47/Wavs/AK-47_Fire_4.AK-47_Fire_4")),
		FSoftObjectPath(TEXT("/Game/AK-47/Sound/AK-47/Wavs/AK-47_Fire_5.AK-47_Fire_5")),
		FSoftObjectPath(TEXT("/Game/AK-47/Sound/AK-47/Wavs/AK-47_Fire_6.AK-47_Fire_6")) };
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Audio")
	float SupportPitch = 0.93f;

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

	/**
	 * Death (presentation, every client; producer: "ragdoll / death animations?"): shortly after death the
	 * body goes limp into a ragdoll, pushed along the killing shot (the soldier parts follow its bones), and
	 * stays in the world for CorpseSeconds after Lyra's death sequence detaches the controller (Lyra hid and
	 * destroyed it at once). Lyra's death cue (GameplayCue.Character.Death: NS_DeathCubes) is refused.
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Death")
	float RagdollDelay = 0.12f;
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Death")
	float RagdollPush = 320.f; // cm/s along the killing shot, applied to the upper body
	UPROPERTY(EditDefaultsOnly, Category = "Tactical|Death")
	float CorpseSeconds = 15.f;

	virtual bool ShouldAcceptGameplayCue(UObject* Self, FGameplayTag GameplayCueTag, EGameplayCueEvent::Type EventType, const FGameplayCueParameters& Parameters) override;

	/** -1 left, 0 none, +1 right. */
	UFUNCTION(BlueprintPure, Category = "Tactical")
	int32 GetLean() const { return Lean; }

protected:
	virtual void OnDeathStarted(AActor* OwningActor) override;
	virtual void OnDeathFinished(AActor* OwningActor) override;

private:
	void StartRagdoll();
	/** Fire cues: Lyra's hidden weapon mesh moved so its Muzzle is on the visible barrel. */
	void AlignLyraMuzzle();
	/** Direction of the last hit taken (from the damage cue), for the ragdoll push. */
	FVector LastShotDirection = FVector::ZeroVector;
	FTimerHandle RagdollTimer;

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
	TArray<TObjectPtr<class USoundBase>> LoadedOpforShots;
	UPROPERTY(Transient)
	TObjectPtr<class USoundBase> LoadedTail;

	bool bLeanLeftHeld = false;
	bool bLeanRightHeld = false;
	FTimerHandle InputContextTimer;
};
