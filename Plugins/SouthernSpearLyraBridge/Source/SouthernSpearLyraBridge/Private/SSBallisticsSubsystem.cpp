// Copyright Southern Spear. All Rights Reserved.

#include "SSBallisticsSubsystem.h"

#include "Components/PrimitiveComponent.h"
#include "GameFramework/Pawn.h"
#include "LandscapeProxy.h"
#include "SSBallistics.h"
#include "Weapons/LyraGameplayAbility_RangedWeapon.h"

namespace
{
	bool Penetrate(const FHitResult& Blocker, const FVector& Direction, FVector& OutResumeAt, float& OutDamageLost)
	{
		const AActor* Actor = Blocker.GetActor();
		UPrimitiveComponent* Surface = Blocker.GetComponent();
		if (!Actor || !Surface || Actor->IsA<APawn>() || Actor->IsA<ALandscapeProxy>())
		{
			return false;
		}
		static const FSSPenetrationTuning Tuning;
		const FVector Dir = Direction.GetSafeNormal();
		const FVector Entry = Blocker.ImpactPoint;
		// Trace back from the far side to find where the bullet leaves this surface.
		FHitResult Exit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(SSPenetration), /*bTraceComplex=*/ true);
		const FVector Far = Entry + Dir * (Tuning.MaxThicknessCm + 1.f);
		if (!Surface->LineTraceComponent(Exit, Far, Entry + Dir * 0.1f, Params))
		{
			return false; // thicker than the limit (or solid all the way)
		}
		if (!FSSPenetrationRules::Penetrates(FVector::Dist(Entry, Exit.ImpactPoint), Tuning, OutDamageLost))
		{
			return false;
		}
		OutResumeAt = FVector(Exit.ImpactPoint) + Dir * 1.f;
		UE_LOG(LogTemp, Verbose, TEXT("SSPenetration %s thickness=%.1f lost=%.2f"), *Actor->GetName(),
			FVector::Dist(Entry, Exit.ImpactPoint), OutDamageLost);
		return true;
	}
}

void USSBallisticsSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	LyraBulletPenetration::SetHook(&Penetrate);
}

void USSBallisticsSubsystem::Deinitialize()
{
	LyraBulletPenetration::SetHook(nullptr);
	Super::Deinitialize();
}
