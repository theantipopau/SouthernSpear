// Copyright Southern Spear. All Rights Reserved.
//
// Spent cases (W3): the casing motion falls under gravity, bounces with restitution and friction,
// comes to rest on a floor, and each weapon throws the right calibre.

#include "Misc/AutomationTest.h"

#include "SSShellEjectSubsystem.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCasingMotionTest, "SouthernSpear.Bridge.Casings.Motion",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSCasingMotionTest::RunTest(const FString& Parameters)
{
	const float Gravity = -980.f;

	// One step: gravity pulls the velocity down, the case moves along it, it ages.
	FSSCasing Case;
	Case.Location = FVector(0.f, 0.f, 100.f);
	Case.Velocity = FVector(300.f, 0.f, 0.f);
	FSSCasingMotion::Step(Case, 0.1f, Gravity);
	TestTrue(TEXT("gravity pulls down"), Case.Velocity.Z < -90.f && Case.Velocity.Z > -100.f);
	TestTrue(TEXT("moves along its velocity"), Case.Location.X > 29.f && Case.Location.X < 30.f && Case.Location.Z < 100.f);
	TestEqual(TEXT("ages"), Case.Age, 0.1f, 1e-5f);

	// A bounce on a floor: the normal part reverses and shrinks, the tangential part loses friction.
	FSSCasing Hit;
	Hit.Velocity = FVector(100.f, 0.f, -300.f);
	Hit.AngularVelocity = FVector(0.f, 0.f, 20.f);
	FSSCasingMotion::Bounce(Hit, FVector::UpVector, 0.35f, 0.35f, 35.f);
	TestEqual(TEXT("bounces up at 35%"), Hit.Velocity.Z, 105.0, 1e-3);
	TestEqual(TEXT("slides at 65%"), Hit.Velocity.X, 65.0, 1e-3);
	TestFalse(TEXT("still moving"), Hit.bResting);
	TestEqual(TEXT("spin damped"), Hit.AngularVelocity.Z, 12.0, 1e-3);
	TestEqual(TEXT("bounce counted"), Hit.Bounces, 1);

	// A slow case settles.
	FSSCasing Slow;
	Slow.Velocity = FVector(10.f, 0.f, -20.f);
	Slow.AngularVelocity = FVector(5.f, 0.f, 0.f);
	FSSCasingMotion::Bounce(Slow, FVector::UpVector);
	TestTrue(TEXT("slow case rests"), Slow.bResting && Slow.Velocity.IsZero() && Slow.AngularVelocity.IsZero());

	// Thrown sideways from shoulder height onto a floor at z = 0, it lands, bounces and rests within 3 s.
	FSSCasing Thrown;
	Thrown.Location = FVector(0.f, 0.f, 140.f);
	Thrown.Velocity = FVector(0.f, 320.f, 80.f);
	float Time = 0.f;
	while (!Thrown.bResting && Time < 3.f)
	{
		FSSCasingMotion::Step(Thrown, 1.f / 60.f, Gravity);
		if (Thrown.Location.Z <= 0.f)
		{
			Thrown.Location.Z = 0.f;
			FSSCasingMotion::Bounce(Thrown, FVector::UpVector);
		}
		Time += 1.f / 60.f;
	}
	TestTrue(TEXT("comes to rest within 3 s"), Thrown.bResting);
	TestTrue(TEXT("bounced before resting"), Thrown.Bounces >= 2);
	TestTrue(TEXT("lands to the side it was thrown, 1-4 m out"), Thrown.Location.Y > 100.f && Thrown.Location.Y < 400.f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSCasingSizeTest, "SouthernSpear.Bridge.Casings.Calibre",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSCasingSizeTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("mesh name to weapon"), FSSCasingMotion::WeaponNameFromMesh(TEXT("SM_A88")), FString(TEXT("A88")));
	TestEqual(TEXT("other names unchanged"), FSSCasingMotion::WeaponNameFromMesh(TEXT("Rifle")), FString(TEXT("Rifle")));
	TestEqual(TEXT("A88 fires 5.56x45"), FSSCasingMotion::SizeFor(TEXT("A88")).Length, 4.5f);
	TestEqual(TEXT("A89 fires 5.56x45"), FSSCasingMotion::SizeFor(TEXT("A89")).Length, 4.5f);
	TestEqual(TEXT("A25 fires 7.62x51"), FSSCasingMotion::SizeFor(TEXT("A25")).Length, 5.1f);
	TestEqual(TEXT("A9 fires 9x19"), FSSCasingMotion::SizeFor(TEXT("A9")).Length, 1.9f);
	TestEqual(TEXT("MAF rifles fire 7.62x39"), FSSCasingMotion::SizeFor(TEXT("MAF_S1")).Length, 3.9f);
	return true;
}

#endif
