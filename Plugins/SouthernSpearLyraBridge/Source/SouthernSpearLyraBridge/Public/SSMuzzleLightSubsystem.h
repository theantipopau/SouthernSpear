// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSMuzzleLightSubsystem.generated.h"

class AActor;
class APawn;
class UPointLightComponent;
class UStaticMeshComponent;

/** One weapon's flash of light. */
struct FSSMuzzleLightSpec
{
	float Candela = 2500.f;   // peak intensity
	float RadiusCm = 700.f;   // attenuation radius
	float Seconds = 0.045f;   // how long it lasts
};

/** Pure muzzle-light rules (W3), tested without a world (SouthernSpear.Bridge.MuzzleLight). */
struct SSBRIDGE_API FSSMuzzleLightRules
{
	/** Intensity at Age seconds into a flash of Peak candela lasting Seconds: a sharp quadratic fall to zero. */
	static float Intensity(float Peak, float Age, float Seconds);

	/** The flash for a weapon by A-series name: a pistol is dimmer and shorter, 7.62x51 brighter and wider. */
	static FSSMuzzleLightSpec SpecFor(const FString& WeaponName);
};

/**
 * The light of a shot (W3): on every client, each rifle or pistol fire cue lights a warm point light at
 * the muzzle of the weapon the viewer sees (first-person view model for the local player, third-person
 * weapon for everyone else) for a few hundredths of a second. It lights the shooter's hands and face and
 * the walls and ground around the muzzle; full-auto fire strobes. Lyra's flash sprite and tracer still play
 * (ASSCharacter::AlignLyraMuzzle keeps them on the visible barrel).
 *
 * Eight pooled lights, no shadows (ss.MuzzleLightShadows 1 turns them on), no new asset. Presentation only
 * (ADR-004); never on a dedicated server. ss.MuzzleLight 0 turns it off.
 */
UCLASS()
class SSBRIDGE_API USSMuzzleLightSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** A shot was fired by Shooter: flash a light at its visible muzzle. */
	void FlashFrom(APawn* Shooter);

private:
	UPointLightComponent* LightComponent(int32 Index);

	struct FLiveFlash
	{
		int32 Light = INDEX_NONE;
		float Age = 0.f;
		float Peak = 0.f;
		float Seconds = 0.f;
	};
	TArray<FLiveFlash> Flashes;
	int32 NextLight = 0;

	UPROPERTY(Transient)
	TObjectPtr<AActor> PoolActor;
	UPROPERTY(Transient)
	TArray<TObjectPtr<UPointLightComponent>> Lights;
};
