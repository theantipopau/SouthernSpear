// Copyright Southern Spear. All Rights Reserved.
//
// Casualty runtime (ADR-040): the settings really loaded from DefaultGame.ini, and the component and kit
// behave as the rules say on a bare world (server authority): a hit down, bleed-out, a treatment that
// finishes, a kit that spends charges, and no health gained without a treatment.

#include "Misc/AutomationTest.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/WorldSettings.h"
#include <initializer_list>
#include "SSCasualtyComponent.h"
#include "SSCasualtySettings.h"
#include "SSMedicalKit.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SSCasualtyTestFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter;

	struct FBareWorld
	{
		UWorld* World = nullptr;
		FBareWorld(const TCHAR* Name)
		{
			World = UWorld::CreateWorld(EWorldType::Game, false, Name);
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			World->GetWorldSettings()->NotifyBeginPlay();
		}
		~FBareWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}
		USSCasualtyComponent* Soldier(const FVector& Location)
		{
			AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), Location, FRotator::ZeroRotator);
			USceneComponent* Root = NewObject<USceneComponent>(Actor, TEXT("Root"));
			Actor->SetRootComponent(Root);
			Root->RegisterComponent();
			Actor->SetActorLocation(Location);
			return USSCasualtyComponent::FindOrAdd(Actor);
		}
		/** Advance the components in 0.1 s steps; the world has no game loop, so tick them by hand. */
		void Advance(std::initializer_list<USSCasualtyComponent*> Components, float Seconds)
		{
			for (float T = 0.f; T < Seconds; T += 0.1f)
			{
				for (USSCasualtyComponent* C : Components)
				{
					C->TickComponent(0.1f, LEVELTICK_All, nullptr);
				}
			}
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCasualtySettingsTest, "SouthernSpear.Casualty.Settings", SSCasualtyTestFlags)

bool FSSCasualtySettingsTest::RunTest(const FString& Parameters)
{
	const USSCasualtySettings& S = USSCasualtySettings::Get();
	TestTrue(TEXT("the head bones imported from DefaultGame.ini (an empty list means the ini line failed)"), S.HeadBones.Num() > 0);
	TestTrue(TEXT("the arm bones imported"), S.ArmBones.Num() > 0);
	TestTrue(TEXT("the leg bones imported"), S.LegBones.Num() > 0);
	TestFalse(TEXT("the kit mesh path imported"), S.KitMesh.IsNull());

	// The ini's numbers are the rules' defaults: one meaning, two places.
	const SSCasualty::FTuning Ini = S.ToTuning();
	const SSCasualty::FTuning Rules;
	TestEqual(TEXT("bleed-out seconds"), Ini.BleedOutSeconds, Rules.BleedOutSeconds);
	TestEqual(TEXT("head multiplier"), Ini.HeadMultiplier, Rules.HeadMultiplier);
	TestEqual(TEXT("teammate stabilise health"), Ini.StabiliseTeammateHealth, Rules.StabiliseTeammateHealth);
	TestEqual(TEXT("kit charges"), Ini.KitCharges, Rules.KitCharges);
	TestEqual(TEXT("dressings carried"), Ini.DressingsCarried, Rules.DressingsCarried);

	// Manny's bone names, as the bridge will pass them from a hit.
	using SSCasualty::EZone;
	TestTrue(TEXT("head"), S.ZoneForBone(TEXT("head")) == EZone::Head);
	TestTrue(TEXT("neck"), S.ZoneForBone(TEXT("neck_01")) == EZone::Head);
	TestTrue(TEXT("spine"), S.ZoneForBone(TEXT("spine_03")) == EZone::Torso);
	TestTrue(TEXT("pelvis"), S.ZoneForBone(TEXT("pelvis")) == EZone::Torso);
	TestTrue(TEXT("upper arm"), S.ZoneForBone(TEXT("upperarm_l")) == EZone::Arm);
	TestTrue(TEXT("hand"), S.ZoneForBone(TEXT("hand_r")) == EZone::Arm);
	TestTrue(TEXT("finger"), S.ZoneForBone(TEXT("index_02_l")) == EZone::Arm);
	TestTrue(TEXT("thigh"), S.ZoneForBone(TEXT("thigh_r")) == EZone::Leg);
	TestTrue(TEXT("calf"), S.ZoneForBone(TEXT("calf_l")) == EZone::Leg);
	TestTrue(TEXT("foot"), S.ZoneForBone(TEXT("foot_l")) == EZone::Leg);
	TestTrue(TEXT("no bone falls to the torso"), S.ZoneForBone(NAME_None) == EZone::Torso);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCasualtyComponentTest, "SouthernSpear.Casualty.Component", SSCasualtyTestFlags)

bool FSSCasualtyComponentTest::RunTest(const FString& Parameters)
{
	using namespace SSCasualty;
	FBareWorld Bare(TEXT("SSCasualtyTestWorld"));
	USSCasualtyComponent* A = Bare.Soldier(FVector::ZeroVector);
	USSCasualtyComponent* B = Bare.Soldier(FVector(100.f, 0.f, 0.f));
	if (!TestNotNull(TEXT("component on A"), A) || !TestNotNull(TEXT("component on B"), B))
	{
		return false;
	}
	TestTrue(TEXT("starts up at full health"), A->GetState() == EState::Up && FMath::IsNearlyEqual(A->GetHealth(), 100.f));
	TestEqual(TEXT("starts with two dressings"), A->GetDressings(), 2);

	// A hit: wounded, bleeding.
	int32 Transitions = 0;
	A->OnTransition.AddLambda([&Transitions](USSCasualtyComponent*, ETransition) { ++Transitions; });
	A->ServerApplyHit(EZone::Leg, 30.f);
	TestTrue(TEXT("a leg hit removes 21"), FMath::IsNearlyEqual(A->GetHealth(), 79.f, 0.01f));
	TestTrue(TEXT("and bleeds"), A->GetBleed() > 0.f);

	// Self-dressing: 6 s, then the bleeding stops, no health returned, one dressing spent.
	const float Before = A->GetHealth();
	TestTrue(TEXT("self-dressing starts"), A->ServerBeginTreatment(A, EAction::Dressing));
	Bare.Advance({ A }, 5.f);
	TestTrue(TEXT("not done at 5 s"), A->IsTreating() && A->GetBleed() > 0.f);
	Bare.Advance({ A }, 1.5f);
	TestFalse(TEXT("done by 6.5 s"), A->IsTreating());
	TestTrue(TEXT("bleeding stopped"), A->GetBleed() == 0.f);
	TestTrue(TEXT("no health came back, only what the bleed took"), A->GetHealth() <= Before);
	TestEqual(TEXT("one dressing left"), A->GetDressings(), 1);

	// No regeneration: 60 s dressed, health never rises.
	const float Held = A->GetHealth();
	Bare.Advance({ A, B }, 60.f);
	TestTrue(TEXT("health is where the dressing left it"), FMath::IsNearlyEqual(A->GetHealth(), Held, 0.001f));

	// Down, then stabilised by a teammate (8 s), who must stay in range; damage cancels it.
	A->ServerApplyHit(EZone::Torso, 200.f);
	TestTrue(TEXT("a lethal torso hit downs"), A->GetState() == EState::Downed);
	TestTrue(TEXT("stabilising starts"), B->ServerBeginTreatment(A, EAction::Stabilise));
	Bare.Advance({ A, B }, 4.f);
	A->ServerApplyHit(EZone::Arm, 1.f);
	TestTrue(TEXT("any hit finishes a downed soldier"), A->GetState() == EState::Dead);
	TestFalse(TEXT("and stops the treatment"), B->IsTreating());

	// A second patient, stabilised to the end.
	USSCasualtyComponent* C = Bare.Soldier(FVector(50.f, 50.f, 0.f));
	C->ServerApplyHit(EZone::Torso, 200.f);
	TestTrue(TEXT("second patient downed"), C->GetState() == EState::Downed);
	TestTrue(TEXT("stabilising starts again"), B->ServerBeginTreatment(C, EAction::Stabilise));
	Bare.Advance({ B, C }, 8.5f);
	TestTrue(TEXT("up after 8 s"), C->GetState() == EState::Up);
	TestTrue(TEXT("at the teammate's 25 health, still bleeding a little"), C->GetHealth() > 20.f && C->GetHealth() <= 25.f && C->GetBleed() > 0.f);
	TestTrue(TEXT("the transition was reported"), Transitions >= 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSMedicalKitTest, "SouthernSpear.Casualty.Kit", SSCasualtyTestFlags)

bool FSSMedicalKitTest::RunTest(const FString& Parameters)
{
	using namespace SSCasualty;
	FBareWorld Bare(TEXT("SSKitTestWorld"));
	USSCasualtyComponent* A = Bare.Soldier(FVector::ZeroVector);
	if (!TestNotNull(TEXT("component"), A))
	{
		return false;
	}
	TestNull(TEXT("no kit yet"), ASSMedicalKit::FindNearest(Bare.World, FVector::ZeroVector, 200.f));
	ASSMedicalKit* Kit = ASSMedicalKit::Drop(Bare.World, FVector(50.f, 0.f, 0.f), nullptr);
	if (!TestNotNull(TEXT("kit dropped"), Kit))
	{
		return false;
	}
	TestEqual(TEXT("eight charges"), Kit->GetCharges(), USSCasualtySettings::Get().KitCharges);
	TestTrue(TEXT("found within range"), ASSMedicalKit::FindNearest(Bare.World, FVector::ZeroVector, 200.f) == Kit);
	TestNull(TEXT("not found out of range"), ASSMedicalKit::FindNearest(Bare.World, FVector(1000.f, 0.f, 0.f), 200.f));

	// Standing beside it heals nothing.
	A->ServerApplyHit(EZone::Torso, 50.f);
	const float Hurt = A->GetHealth();
	Bare.Advance({ A }, 30.f);
	TestTrue(TEXT("no passive healing beside a kit"), A->GetHealth() <= Hurt);

	// Take a dressing (after spending one, so there is room), then treat at the kit.
	A->ServerBeginTreatment(A, EAction::Dressing);
	Bare.Advance({ A }, 6.5f);
	TestEqual(TEXT("one dressing left"), A->GetDressings(), 1);
	TestTrue(TEXT("take a dressing from the kit"), A->ServerTakeDressingFromKit());
	TestEqual(TEXT("back to two"), A->GetDressings(), 2);
	TestEqual(TEXT("it cost a charge"), Kit->GetCharges(), 7);
	TestFalse(TEXT("not beyond the carry limit"), A->ServerTakeDressingFromKit());

	TestTrue(TEXT("treat at the kit"), A->ServerBeginTreatment(A, EAction::KitSelfTreat));
	Bare.Advance({ A }, 8.5f);
	TestTrue(TEXT("60 health from the kit"), FMath::IsNearlyEqual(A->GetHealth(), 60.f, 0.01f) && A->GetBleed() == 0.f);
	TestEqual(TEXT("another charge"), Kit->GetCharges(), 6);
	return true;
}

#endif
