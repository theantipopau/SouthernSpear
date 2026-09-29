// Copyright Southern Spear. All Rights Reserved.
//
// Left-hand IK (W2): the pure two-bone solve on a component-space arm puts the hand on a reachable
// target, keeps bone lengths, keeps the hand's rotation, carries fingers and twist bones with their
// bones, stops at full reach, blends by alpha, and refuses a broken chain. The rotation step (Session
// 070) then turns the hand to the target's rotation and carries its descendants, so the palm follows
// the grip socket instead of lying open on the receiver.

#include "Misc/AutomationTest.h"

#include "SSHandIKMeshComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	// root(0) -> clavicle(1) -> upperarm(2) -> lowerarm(3) -> hand(4) -> finger(5); upperarm -> twist(6)
	void MakeArm(TArray<FTransform>& Pose, TArray<int32>& Parents)
	{
		Parents = { INDEX_NONE, 0, 1, 2, 3, 4, 2 };
		const FQuat HandRot = FQuat(FVector(0, 0, 1), FMath::DegreesToRadians(20.f));
		Pose = {
			FTransform(FVector(0, 0, 0)),
			FTransform(FVector(0, 10, 140)),
			FTransform(FVector(0, 20, 140)),
			FTransform(FQuat::Identity, FVector(0, 48, 130)),   // elbow: 29.7 cm, bent down and out
			FTransform(HandRot, FVector(20, 60, 115)),          // wrist: 26.0 cm on
			FTransform(HandRot, FVector(28, 62, 114)),          // a finger off the hand
			FTransform(FVector(0, 34, 135)),                    // upperarm twist
		};
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHandIKSolveTest, "SouthernSpear.Bridge.HandIK.Solve",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSHandIKSolveTest::RunTest(const FString& Parameters)
{
	TArray<FTransform> Pose;
	TArray<int32> Parents;
	MakeArm(Pose, Parents);
	const TArray<FTransform> Before = Pose;
	const double L1 = FVector::Distance(Before[2].GetLocation(), Before[3].GetLocation());
	const double L2 = FVector::Distance(Before[3].GetLocation(), Before[4].GetLocation());

	// A reachable target in front of the chest.
	const FVector Target(35.f, 30.f, 125.f);
	TestTrue(TEXT("solve applies"), FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Target, 1.f));
	TestTrue(TEXT("hand on the target"), Pose[4].GetLocation().Equals(Target, 0.05f));
	TestTrue(TEXT("shoulder does not move"), Pose[2].GetLocation().Equals(Before[2].GetLocation(), 1e-3f));
	TestEqual(TEXT("upper arm length kept"), FVector::Distance(Pose[2].GetLocation(), Pose[3].GetLocation()), L1, 0.01);
	TestEqual(TEXT("forearm length kept"), FVector::Distance(Pose[3].GetLocation(), Pose[4].GetLocation()), L2, 0.01);
	TestTrue(TEXT("hand keeps its animated rotation"), Pose[4].GetRotation().Equals(Before[4].GetRotation(), 1e-4f));
	TestTrue(TEXT("finger carried with the hand"),
		Pose[5].GetRelativeTransform(Pose[4]).Equals(Before[5].GetRelativeTransform(Before[4]), 1e-3f));
	TestTrue(TEXT("twist bone carried with the upper arm"),
		Pose[6].GetRelativeTransform(Pose[2]).Equals(Before[6].GetRelativeTransform(Before[2]), 1e-3f));
	TestTrue(TEXT("bones outside the arm untouched"), Pose[1].Equals(Before[1], 1e-6f) && Pose[0].Equals(Before[0], 1e-6f));
	// The upper arm's own axis now points at the new elbow (the bone rotation matches its child's position).
	const FVector UpperAxisBefore = Before[2].GetRotation().UnrotateVector(Before[3].GetLocation() - Before[2].GetLocation());
	const FVector UpperAxisAfter = Pose[2].GetRotation().UnrotateVector(Pose[3].GetLocation() - Pose[2].GetLocation());
	TestTrue(TEXT("elbow stays on the upper arm's axis"), UpperAxisBefore.Equals(UpperAxisAfter, 0.01f));
	const FVector LowerAxisBefore = Before[3].GetRotation().UnrotateVector(Before[4].GetLocation() - Before[3].GetLocation());
	const FVector LowerAxisAfter = Pose[3].GetRotation().UnrotateVector(Pose[4].GetLocation() - Pose[3].GetLocation());
	TestTrue(TEXT("wrist stays on the forearm's axis"), LowerAxisBefore.Equals(LowerAxisAfter, 0.01f));

	// Out of reach: the hand stops at full reach along the line, no stretching.
	MakeArm(Pose, Parents);
	const FVector Far(200.f, 20.f, 140.f);
	TestTrue(TEXT("far solve applies"), FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Far, 1.f));
	const double Reach = FVector::Distance(Pose[2].GetLocation(), Pose[4].GetLocation());
	TestTrue(TEXT("full reach, not stretched"), Reach <= L1 + L2 + 0.01 && Reach >= L1 + L2 - 0.05);
	TestTrue(TEXT("pointing at the far target"),
		((Pose[4].GetLocation() - Pose[2].GetLocation()).GetSafeNormal() | (Far - Pose[2].GetLocation()).GetSafeNormal()) > 0.9999);

	// Alpha: half-way blends the effector half-way.
	MakeArm(Pose, Parents);
	FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Target, 0.5f);
	TestTrue(TEXT("alpha 0.5 lands half-way"), Pose[4].GetLocation().Equals(FMath::Lerp(Before[4].GetLocation(), Target, 0.5f), 0.05f));

	// Refusals leave the pose untouched.
	MakeArm(Pose, Parents);
	TestFalse(TEXT("alpha 0 does nothing"), FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Target, 0.f));
	TestFalse(TEXT("a broken chain is refused"), FSSHandIK::Apply(Pose, Parents, 2, 6, 4, Target, 1.f));
	TestFalse(TEXT("mismatched parents are refused"), FSSHandIK::Apply(Pose, TArray<int32>{ INDEX_NONE }, 2, 3, 4, Target, 1.f));
	bool bSame = true;
	for (int32 Bone = 0; Bone < Pose.Num(); ++Bone)
	{
		bSame &= Pose[Bone].Equals(Before[Bone], 1e-6f);
	}
	TestTrue(TEXT("refusals leave the pose as it was"), bSame);
	return true;
}

// The hand's rotation step: a wrist-only solve leaves the palm open, so the hand is turned to the
// grip socket's rotation (socket rotation * per-skeleton offset) and everything under the hand follows.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHandIKRotateTest, "SouthernSpear.Bridge.HandIK.RotateHand",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSHandIKRotateTest::RunTest(const FString& Parameters)
{
	TArray<FTransform> Pose;
	TArray<int32> Parents;
	const FQuat Target = FRotator(35.f, -20.f, 70.f).Quaternion();

	// At alpha 1 the hand's rotation is the target's, and its position is left alone.
	MakeArm(Pose, Parents);
	const TArray<FTransform> Before = Pose;
	TestTrue(TEXT("rotate applies"), FSSHandIK::RotateChain(Pose, Parents, 4, Target, 1.f));
	TestTrue(TEXT("the hand matches the target at alpha 1"), Pose[4].GetRotation().Equals(Target, 1e-4f));
	TestTrue(TEXT("the hand keeps the position the solve gave it"), Pose[4].GetLocation().Equals(Before[4].GetLocation(), 1e-6f));
	TestTrue(TEXT("a finger follows with its own local transform"),
		Pose[5].GetRelativeTransform(Pose[4]).Equals(Before[5].GetRelativeTransform(Before[4]), 1e-5f));
	TestTrue(TEXT("bones outside the hand are untouched"),
		Pose[0].Equals(Before[0], 1e-6f) && Pose[1].Equals(Before[1], 1e-6f)
			&& Pose[2].Equals(Before[2], 1e-6f) && Pose[3].Equals(Before[3], 1e-6f)
			&& Pose[6].Equals(Before[6], 1e-6f));

	// Both steps together: the hand is on the grip with the grip's rotation (what the component does).
	MakeArm(Pose, Parents);
	const FVector TargetLocation(35.f, 30.f, 125.f);
	TestTrue(TEXT("solve then rotate both apply"),
		FSSHandIK::Apply(Pose, Parents, 2, 3, 4, TargetLocation, 1.f)
			&& FSSHandIK::RotateChain(Pose, Parents, 4, Target, 1.f));
	TestTrue(TEXT("hand on the grip"), Pose[4].GetLocation().Equals(TargetLocation, 0.05f));
	TestTrue(TEXT("hand turned to the grip"), Pose[4].GetRotation().Equals(Target, 1e-4f));

	// Alpha blends the rotation the same way it blends the position.
	MakeArm(Pose, Parents);
	FSSHandIK::RotateChain(Pose, Parents, 4, Target, 0.5f);
	TestTrue(TEXT("alpha 0.5 is half-way round"),
		Pose[4].GetRotation().Equals(FQuat::Slerp(Before[4].GetRotation(), Target, 0.5f), 1e-4f));

	// A zero offset (the config default) reproduces the socket's rotation exactly.
	MakeArm(Pose, Parents);
	const FQuat SocketRotation = FRotator(12.f, 88.f, -3.f).Quaternion();
	const FQuat WithOffset = SocketRotation * FRotator::ZeroRotator.Quaternion();
	FSSHandIK::RotateChain(Pose, Parents, 4, WithOffset, 1.f);
	TestTrue(TEXT("a zero offset keeps the socket's own rotation"), Pose[4].GetRotation().Equals(SocketRotation, 1e-4f));

	// Refusals leave the pose untouched.
	MakeArm(Pose, Parents);
	TestFalse(TEXT("alpha 0 does nothing"), FSSHandIK::RotateChain(Pose, Parents, 4, Target, 0.f));
	TestFalse(TEXT("a bad hand index is refused"), FSSHandIK::RotateChain(Pose, Parents, 99, Target, 1.f));
	TestFalse(TEXT("mismatched parents are refused"),
		FSSHandIK::RotateChain(Pose, TArray<int32>{ INDEX_NONE }, 4, Target, 1.f));
	bool bSame = true;
	for (int32 Bone = 0; Bone < Pose.Num(); ++Bone)
	{
		bSame &= Pose[Bone].Equals(Before[Bone], 1e-6f);
	}
	TestTrue(TEXT("refusals leave the pose as it was"), bSame);
	return true;
}

#endif
