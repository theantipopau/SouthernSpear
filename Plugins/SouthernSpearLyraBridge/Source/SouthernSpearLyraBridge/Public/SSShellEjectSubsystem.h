// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSShellEjectSubsystem.generated.h"

class AActor;
class APawn;
class UMaterialInstanceDynamic;
class UStaticMesh;
class UStaticMeshComponent;

/** One spent case in flight or at rest. */
struct FSSCasing
{
	FVector Location = FVector::ZeroVector;
	FVector Velocity = FVector::ZeroVector;     // cm/s
	FQuat Rotation = FQuat::Identity;
	FVector AngularVelocity = FVector::ZeroVector; // rad/s
	float Age = 0.f;
	int32 Bounces = 0;
	bool bResting = false;
};

/** Case size, cm. */
struct FSSCasingSize
{
	float Diameter = 0.96f;
	float Length = 4.5f;
};

/** Pure casing rules (W3), tested without a world (SouthernSpear.Bridge.Casings). */
struct SSBRIDGE_API FSSCasingMotion
{
	/** Integrate one step: gravity (GravityZ, cm/s^2, negative is down), light air drag, spin. */
	static void Step(FSSCasing& Casing, float DeltaSeconds, float GravityZ);

	/**
	 * Bounce off a surface with outward Normal: the normal part of the velocity reverses and is scaled by
	 * Restitution, the tangential part loses Friction (0..1), and the spin is damped. A case slower than
	 * RestSpeed after the bounce comes to rest.
	 */
	static void Bounce(FSSCasing& Casing, const FVector& Normal, float Restitution = 0.35f, float Friction = 0.35f,
		float RestSpeed = 35.f);

	/** The case for a weapon, from its A-series name (the mesh SM_<Name>): 5.56 by default. */
	static FSSCasingSize SizeFor(const FString& WeaponName);

	/** "SM_A88" -> "A88"; anything else unchanged. */
	static FString WeaponNameFromMesh(const FString& MeshName);
};

/**
 * Spent cases thrown from the held weapon's ejection port (W3, WEAPONS_ANIMATION_PLAN).
 *
 * On every client (never a dedicated server), ASSCharacter reports each rifle or pistol fire cue here.
 * The case leaves the weapon's Eject socket towards its EjectEnd socket (the ADFRC memory points
 * nabojnicestart / nabojniceend, Tools/Blender/adfrc_weapon.py), with the shooter's velocity, flies
 * ballistically, bounces off the world (a line trace per moving case) and lies where it lands until
 * its pool slot is reused. The local player's cases come from the first-person weapon, everyone
 * else's from the third-person one. A weapon without the sockets throws nothing.
 *
 * Presentation only (ADR-004): no collision, no gameplay effect. The case is the engine cylinder in
 * brass, sized per calibre; no new asset. ss.Casings 0 turns it off.
 */
UCLASS()
class SSBRIDGE_API USSShellEjectSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** A shot was fired by Shooter: throw one case from its visible weapon. */
	void EjectFrom(APawn* Shooter);

	/** Cases currently in the pool (tests, diagnostics). */
	int32 NumActive() const { return Casings.Num(); }

private:
	/** The static mesh component with the Eject socket that the local viewer sees for this shooter. */
	UStaticMeshComponent* FindEjectingWeapon(APawn* Shooter) const;
	UStaticMeshComponent* CaseComponent(int32 Index);

	struct FLiveCasing
	{
		FSSCasing Motion;
		TWeakObjectPtr<AActor> Shooter;
		int32 Slot = INDEX_NONE;
		float Diameter = 1.f; // cm: rest height above the surface
	};
	TArray<FLiveCasing> Casings;
	int32 NextSlot = 0;

	UPROPERTY(Transient)
	TObjectPtr<AActor> PoolActor;
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Pool;
	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> CaseMesh;
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> Brass;
};
