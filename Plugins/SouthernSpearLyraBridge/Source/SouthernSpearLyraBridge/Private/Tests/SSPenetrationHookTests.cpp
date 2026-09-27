// Copyright Southern Spear. All Rights Reserved.
//
// Bullet penetration hook (ADR-026, D-09): the hook Lyra's ranged weapon calls is registered, lets a
// bullet through a 5 cm board with the rule's damage loss, and stops it at a 40 cm block.

#include "Misc/AutomationTest.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "SSBallistics.h"
#include "Weapons/LyraGameplayAbility_RangedWeapon.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	AStaticMeshActor* SpawnBoard(UWorld* World, UStaticMesh* Cube, float ThicknessCm)
	{
		// The engine cube is 100 cm, centred; X is the shot axis.
		FActorSpawnParameters Params;
		AStaticMeshActor* Board = World->SpawnActor<AStaticMeshActor>(FVector::ZeroVector, FRotator::ZeroRotator, Params);
		UStaticMeshComponent* Mesh = Board->GetStaticMeshComponent();
		Mesh->SetMobility(EComponentMobility::Movable);
		Mesh->SetStaticMesh(Cube);
		Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		Board->SetActorScale3D(FVector(ThicknessCm / 100.f, 2.f, 2.f));
		Mesh->RecreatePhysicsState();
		return Board;
	}

	bool Shoot(AStaticMeshActor* Board, float ThicknessCm, FVector& OutResume, float& OutLost)
	{
		const FVector Dir(1.f, 0.f, 0.f);
		const FHitResult Blocker(Board, Board->GetStaticMeshComponent(), FVector(-ThicknessCm * 0.5f, 0.f, 0.f), -Dir);
		return LyraBulletPenetration::GetHook()(Blocker, Dir, OutResume, OutLost);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPenetrationHookTest, "SouthernSpear.Bridge.Ballistics.PenetrationHook",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSPenetrationHookTest::RunTest(const FString& Parameters)
{
	if (!TestTrue(TEXT("the bridge registered Lyra's penetration hook"), (bool)LyraBulletPenetration::GetHook()))
	{
		return false;
	}
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (!TestNotNull(TEXT("engine cube"), Cube))
	{
		return false;
	}
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("SSPenetrationTestWorld"));
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);

	const FSSPenetrationTuning Tuning;
	float Expected = 0.f;
	FSSPenetrationRules::Penetrates(5.f, Tuning, Expected);

	FVector Resume;
	float Lost = 0.f;
	AStaticMeshActor* Board = SpawnBoard(World, Cube, 5.f);
	const bool bThrough = Shoot(Board, 5.f, Resume, Lost);
	TestTrue(TEXT("a 5 cm board is penetrated"), bThrough);
	TestTrue(TEXT("damage lost matches the 5 cm rule"), FMath::IsNearlyEqual(Lost, Expected, 0.02f));
	TestTrue(TEXT("the trace resumes beyond the board"), Resume.X > 2.5f && Resume.X < 5.f);
	AddInfo(FString::Printf(TEXT("5 cm board: damage lost %.3f (expected %.3f), resume x=%.2f; A88 torso 38 -> %.1f"),
		Lost, Expected, Resume.X, 38.f * (1.f - Lost)));
	Board->Destroy();

	AStaticMeshActor* Block = SpawnBoard(World, Cube, 40.f);
	TestFalse(TEXT("a 40 cm block stops the bullet"), Shoot(Block, 40.f, Resume, Lost));

	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif
