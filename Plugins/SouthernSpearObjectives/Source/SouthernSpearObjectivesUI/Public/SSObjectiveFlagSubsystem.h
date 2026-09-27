// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSObjectiveFlagSubsystem.generated.h"

class ASSObjectiveActor;
class USkeletalMeshComponent;
class UStaticMeshComponent;

/**
 * Client presentation: a flagpole on each objective. The flag shown is
 * relative to the local viewer: the viewer's own side flies the friendly flag
 * (Australian), the other side the fictional MAF flag; a neutral, uncontested
 * objective has a bare pole. The flag rises with capture progress and lowers
 * as the holder loses it. Reads replicated objective state only; spawns
 * local, collision-free actors; never touches gameplay.
 */
UCLASS()
class SSOBJUI_API USSObjectiveFlagSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

private:
	struct FFlag
	{
		TWeakObjectPtr<ASSObjectiveActor> Objective;
		TWeakObjectPtr<AActor> Actor;
		TWeakObjectPtr<USkeletalMeshComponent> Cloth;
		float Height = 0.f;
		int32 LastShown = -1; // flag on the pole, for the change log
	};
	TArray<FFlag> Flags;
	bool bSpawned = false;
};
