// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSLocalHudState.generated.h"

/**
 * What the local player's HUD shows, as plain values. The Lyra bridge fills
 * it from the gameplay systems each frame; UI modules only read it, so no UI
 * module ever depends on Lyra (ADR-019, guard SS002/SS005). Client-local,
 * never replicated, never read by gameplay (ADR-004).
 */
UCLASS()
class SSCORE_API USSLocalHudState : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	/** False while there is no local pawn (dead, spectating, loading). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	bool bHasPawn = false;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	float Health = 0.f;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	float MaxHealth = 0.f;

	/** -1 when the held item has no ammunition. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	int32 Magazine = -1;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	int32 Reserve = -1;

	/** Full magazine size; -1 when unknown. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	int32 MagazineSize = -1;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	FText WeaponName;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	bool bAiming = false;

	/** Set by the match menu's RE-DEPLOY; the bridge consumes it (asks the server to end this life so the
	 * player respawns with the selected class) and clears it. A request only: the server decides. */
	UPROPERTY(Transient, BlueprintReadWrite, Category = "HUD")
	bool bRedeployRequested = false;
	/** World seconds of the last RE-DEPLOY request (-1 never): the death that follows is not "killed in action". */
	UPROPERTY(Transient, BlueprintReadWrite, Category = "HUD")
	double LastRedeployTime = -1.0;
	/** When the local player was last hit (world seconds; -1 never) and from where (the shooter's
	 * trace start). Filled by the bridge from Lyra's damage cue; drives the HUD hit direction arrow. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	double LastHitTime = -1.0;
	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	FVector LastHitFrom = FVector::ZeroVector;

	/** Magnification of the held weapon's optic (0: iron or red-dot sight, aimed over the view model). Filled by
	 * the bridge from OpticMagnification(WeaponName). Aiming with it > 1 shows the scope view (HUD overlay). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "HUD")
	float OpticMagnification = 0.f;

	/** The fitted optic by weapon display name (Tools/build_adfrc_weapons.py): A25 marksman TA648 6x; the A88
	 * family Spectr and the A4 / A416 TA31 4x; the A89 C79 3.4x; others (pistols) 0. Cosmetic view only
	 * (ADR-004): recoil, spread and damage are untouched. */
	static float OpticMagnificationFor(const FString& WeaponName)
	{
		const FString Name = WeaponName.ToUpper();
		if (Name.StartsWith(TEXT("A25")))
		{
			return 6.f;
		}
		if (Name.StartsWith(TEXT("A89")))
		{
			return 3.4f;
		}
		if (Name.StartsWith(TEXT("A88")) || Name.StartsWith(TEXT("A416")) || Name.StartsWith(TEXT("A4")))
		{
			return 4.f;
		}
		return 0.f;
	}

	/** Bearing of a hit source from the camera, in degrees: 0 ahead, +90 right, -90 left, 180 behind. */
	static float HitBearing(const FVector& CameraLocation, float CameraYaw, const FVector& From)
	{
		const FVector Rel = FRotator(0.f, CameraYaw, 0.f).UnrotateVector(From - CameraLocation);
		return FMath::RadiansToDegrees(FMath::Atan2(Rel.Y, Rel.X));
	}

	float GetHealthFraction() const { return MaxHealth > 0.f ? FMath::Clamp(Health / MaxHealth, 0.f, 1.f) : 0.f; }
};
